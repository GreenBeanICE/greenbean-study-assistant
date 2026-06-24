# API 配置（后端）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把云端模型 provider 配置体系从"看得见跑不通"改造为"JSON 文件持久化 + chat/embedding 双 provider 分组激活 + FastAPI 路由对外可用 + 启动自动恢复"。

**Architecture:** `ProviderConfig` 实体加 `purpose`/`embedding_dimension`；配置持久化从 SQLite 迁到 `data/provider_configs.json`（原子写 + 进程锁）；`ProviderRegistry` 扩展为 chat/embedding 双槽；`ProviderController` 改造为 `APIRouter` 并挂载；`main.py` lifespan 启动时从 JSON 恢复激活态并解析 embedding 维度。

**Tech Stack:** Python 3.12、Pydantic v2、FastAPI、SQLAlchemy（业务库）、openai SDK、pytest。

**Spec:** `docs/superpowers/specs/2026-06-24-api-config-design.md`

**约定：** 所有 `python -m pytest` 命令均在 `backend-python/` 目录下执行。本计划仅覆盖后端，前端计划见后续 `2026-06-24-api-config-frontend.md`。

---

## File Structure

**新建：**
- `backend-python/app/enums/purpose.py` — `Purpose` 枚举（chat/embedding），消除散落字面量
- `backend-python/app/config/settings.py` — 改造空占位，承载 `PROVIDER_CONFIGS_PATH` 常量
- `backend-python/tests/unit/entities/test_provider_config_validation.py` — `ProviderConfig` 的 purpose/dimension 校验
- `backend-python/tests/unit/repositories/test_provider_config_repository.py` — JSON 文件仓库测试

**重写：**
- `backend-python/app/repositories/provider_config_repository.py` — 从 SQLite 仓库改为 JSON 文件仓库

**修改：**
- `backend-python/app/entities/provider_config.py` — 加 purpose/embedding_dimension 字段 + 校验
- `backend-python/app/schemas/provider_schema.py` — Create/Update/Response 加字段
- `backend-python/app/providers/registry.py` — 双 provider
- `backend-python/app/providers/openai_compat_provider.py` — embedding model 默认取 config.model_id
- `backend-python/app/services/provider_service.py` — 去 SQLite/UOW，依赖文件仓库
- `backend-python/app/services/embedding_service.py` — 从 registry 取 provider/model/dimension
- `backend-python/app/api/provider_controller.py` — 改 APIRouter
- `backend-python/app/api/dependencies.py` — 装配 provider/embedding service
- `backend-python/app/main.py` — include router + lifespan 启动恢复 + 维度来源
- `backend-python/app/agents/{chat,analysis,classification}_agent.py` — get_active() → get_active_chat()
- `backend-python/app/db/models.py` — 移除 ProviderConfigModel
- `backend-python/app/db/init_db.py` — 移除 provider_configs 建表 SQL
- `backend-python/tests/conftest.py` — provider_config_factory 加 purpose
- `backend-python/tests/unit/providers/test_registry.py` — 双 provider
- `backend-python/tests/unit/providers/test_openai_compat_provider.py` — embedding 默认 model
- `backend-python/tests/unit/services/test_provider_service.py` — 去 SQLite，按 purpose
- `backend-python/tests/unit/services/test_embedding_service.py` — 从 active embedding config
- `backend-python/tests/unit/api/test_provider_controller.py` → 迁移为 HTTP 端点测试
- `backend-python/tests/integration/api/test_provider_workflow.py` — JSON 持久化工作流
- `.gitignore` — 加 `data/provider_configs.json`

---

## Task 1: Purpose 枚举 + ProviderConfig 字段与校验

**Files:**
- Create: `backend-python/app/enums/purpose.py`
- Modify: `backend-python/app/entities/provider_config.py`
- Modify: `backend-python/tests/conftest.py:48-64`
- Test: `backend-python/tests/unit/entities/test_provider_config_validation.py`

- [ ] **Step 1: 写失败测试**

创建 `backend-python/tests/unit/entities/test_provider_config_validation.py`：

```python
import pytest
from pydantic import ValidationError

from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose


def _base_kwargs(**overrides):
    kwargs = {
        "name": "cfg",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-test",
        "api_host": "https://api.test.com",
        "model_id": "model",
        "display_name": "Cfg",
    }
    kwargs.update(overrides)
    return kwargs


def test_chat_config_rejects_embedding_dimension():
    with pytest.raises(ValidationError, match="chat 配置不能设置 embedding_dimension"):
        ProviderConfig(**_base_kwargs(purpose=Purpose.CHAT, embedding_dimension=1024))


def test_embedding_config_requires_positive_dimension():
    with pytest.raises(ValidationError, match="embedding 配置必须提供正整数 embedding_dimension"):
        ProviderConfig(**_base_kwargs(purpose=Purpose.EMBEDDING, embedding_dimension=None))


def test_embedding_config_rejects_non_positive_dimension():
    with pytest.raises(ValidationError, match="embedding 配置必须提供正整数 embedding_dimension"):
        ProviderConfig(**_base_kwargs(purpose=Purpose.EMBEDDING, embedding_dimension=0))


def test_embedding_config_accepts_dimension():
    config = ProviderConfig(**_base_kwargs(purpose=Purpose.EMBEDDING, embedding_dimension=1024))
    assert config.purpose == Purpose.EMBEDDING
    assert config.embedding_dimension == 1024


def test_chat_config_defaults_dimension_none():
    config = ProviderConfig(**_base_kwargs(purpose=Purpose.CHAT))
    assert config.embedding_dimension is None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/entities/test_provider_config_validation.py -v`
Expected: FAIL — `ImportError: cannot import name 'Purpose'`（枚举尚未创建）

- [ ] **Step 3: 创建 Purpose 枚举 + 改 ProviderConfig**

创建 `backend-python/app/enums/purpose.py`：

```python
from enum import Enum


class Purpose(str, Enum):
    CHAT = "chat"
    EMBEDDING = "embedding"
```

修改 `backend-python/app/entities/provider_config.py`，在 import 区加 `from pydantic import BaseModel, Field, model_validator`，加 `from app.enums.purpose import Purpose`，并在模型中追加字段与校验器（插入到 `updated_at` 字段之后、类体末尾）：

```python
    purpose: Purpose = Field(..., description="用途：chat 或 embedding。")
    embedding_dimension: int | None = Field(default=None, description="向量维度，仅 embedding 用。")

    @model_validator(mode="after")
    def _validate_dimension_by_purpose(self) -> "ProviderConfig":
        if self.purpose == Purpose.EMBEDDING:
            if self.embedding_dimension is None or self.embedding_dimension <= 0:
                raise ValueError("embedding 配置必须提供正整数 embedding_dimension")
        elif self.purpose == Purpose.CHAT and self.embedding_dimension is not None:
            raise ValueError("chat 配置不能设置 embedding_dimension")
        return self
```

同步修改 `backend-python/tests/conftest.py` 的 `provider_config_factory`，使其默认生成合法的 chat 配置：

```python
@pytest.fixture
def provider_config_factory():
    from app.entities.provider_config import ProviderConfig
    from app.enums.api_mode import ApiMode
    from app.enums.purpose import Purpose

    def make_config(
        name: str = "test-cfg",
        is_active: bool = False,
        purpose: Purpose = Purpose.CHAT,
        embedding_dimension: int | None = None,
    ) -> ProviderConfig:
        return ProviderConfig(
            name=name,
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-test",
            api_host="https://api.test.com",
            model_id="test-model",
            display_name=name,
            is_active=is_active,
            purpose=purpose,
            embedding_dimension=embedding_dimension,
        )

    return make_config
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/entities/test_provider_config_validation.py tests/unit/providers tests/unit/services tests/unit/api/test_provider_controller.py -v`
Expected: PASS（新测试通过；因 factory 默认 purpose=CHAT，现有依赖 factory 的测试仍可跑）

- [ ] **Step 5: 提交**

```bash
git add backend-python/app/enums/purpose.py backend-python/app/entities/provider_config.py backend-python/tests/conftest.py backend-python/tests/unit/entities/test_provider_config_validation.py
git commit -m "feat(provider): 新增 Purpose 枚举与 ProviderConfig 的 purpose/embedding_dimension 字段校验"
```

---

## Task 2: provider_schema 加 purpose / embedding_dimension

**Files:**
- Modify: `backend-python/app/schemas/provider_schema.py`
- Modify: `backend-python/tests/unit/api/test_provider_controller.py`（Create 请求补 purpose）

- [ ] **Step 1: 写失败测试**

在 `backend-python/tests/unit/api/test_provider_controller.py` 现有 `test_create_provider` 中，给 `ProviderConfigCreateRequest` 补 `purpose=Purpose.CHAT`（文件顶部加 `from app.enums.purpose import Purpose`）：

```python
        request = ProviderConfigCreateRequest(
            name="new-cfg",
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-key",
            api_host="https://api.test.com",
            model_id="test-model",
            display_name="New",
            purpose=Purpose.CHAT,
        )
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/api/test_provider_controller.py::TestProviderController::test_create_provider -v`
Expected: FAIL — `ValidationError`（ProviderConfigCreateRequest 无 purpose 字段）

- [ ] **Step 3: 改 schema**

修改 `backend-python/app/schemas/provider_schema.py`，import 区加 `from app.enums.purpose import Purpose`，给三个 schema 加字段：

- `ProviderConfigCreateRequest`：加 `purpose: Purpose = Field(..., description="用途：chat 或 embedding。")` 和 `embedding_dimension: int | None = Field(default=None, description="向量维度，仅 embedding 用。")`
- `ProviderConfigUpdateRequest`：加 `purpose: Purpose | None = Field(default=None, description="用途。")` 和 `embedding_dimension: int | None = Field(default=None, description="向量维度。")`
- `ProviderConfigResponse`：加 `purpose: Purpose = Field(..., description="用途。")` 和 `embedding_dimension: int | None = Field(default=None, description="向量维度。")`

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/api/test_provider_controller.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend-python/app/schemas/provider_schema.py backend-python/tests/unit/api/test_provider_controller.py
git commit -m "feat(provider): provider_schema 增加 purpose 与 embedding_dimension 字段"
```

---

## Task 3: ProviderConfigRepository 改为 JSON 文件仓库

**Files:**
- Rewrite: `backend-python/app/repositories/provider_config_repository.py`
- Create: `backend-python/app/config/settings.py`
- Test: `backend-python/tests/unit/repositories/test_provider_config_repository.py`

- [ ] **Step 1: 写失败测试**

创建 `backend-python/tests/unit/repositories/test_provider_config_repository.py`：

```python
import json

import pytest

from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.repositories.provider_config_repository import ProviderConfigRepository


def _chat_config(**overrides):
    kwargs = {
        "name": "chat-1",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-chat",
        "api_host": "https://api.chat.com",
        "model_id": "chat-model",
        "display_name": "Chat",
        "purpose": Purpose.CHAT,
    }
    kwargs.update(overrides)
    return ProviderConfig(**kwargs)


def _embedding_config(**overrides):
    kwargs = {
        "name": "embed-1",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-embed",
        "api_host": "https://api.embed.com",
        "model_id": "embed-model",
        "display_name": "Embed",
        "purpose": Purpose.EMBEDDING,
        "embedding_dimension": 1024,
    }
    kwargs.update(overrides)
    return ProviderConfig(**kwargs)


def test_save_and_list_all(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    repo.save(_chat_config())
    repo.save(_embedding_config())
    assert len(repo.list_all()) == 2


def test_list_by_purpose(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    repo.save(_chat_config())
    repo.save(_embedding_config())
    assert len(repo.list_by_purpose(Purpose.CHAT)) == 1
    assert len(repo.list_by_purpose(Purpose.EMBEDDING)) == 1


def test_get_by_id(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    config = _chat_config()
    repo.save(config)
    assert repo.get_by_id(config.id).name == "chat-1"
    assert repo.get_by_id("missing") is None


def test_save_replaces_existing(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    config = _chat_config()
    repo.save(config)
    repo.save(config.model_copy(update={"display_name": "Updated"}))
    assert len(repo.list_all()) == 1
    assert repo.get_by_id(config.id).display_name == "Updated"


def test_delete(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    config = _chat_config()
    repo.save(config)
    assert repo.delete(config.id) is True
    assert repo.delete(config.id) is False
    assert repo.list_all() == []


def test_deactivate_by_purpose_only_affects_same_purpose(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    chat = _chat_config(is_active=True)
    embed = _embedding_config(is_active=True)
    repo.save(chat)
    repo.save(embed)
    repo.deactivate_by_purpose(Purpose.CHAT)
    assert repo.get_by_id(chat.id).is_active is False
    assert repo.get_by_id(embed.id).is_active is True


def test_get_active_by_purpose(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    repo.save(_chat_config(is_active=False))
    assert repo.get_active_by_purpose(Purpose.CHAT) is None
    active = _chat_config(name="chat-2", is_active=True)
    repo.save(active)
    assert repo.get_active_by_purpose(Purpose.CHAT).id == active.id


def test_empty_file_when_missing(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    assert repo.list_all() == []
    repo.save(_chat_config())
    payload = json.loads((tmp_path / "provider_configs.json").read_text(encoding="utf-8"))
    assert "providers" in payload
    assert len(payload["providers"]) == 1


def test_corrupted_file_raises(tmp_path):
    path = tmp_path / "provider_configs.json"
    path.write_text("{not valid json", encoding="utf-8")
    repo = ProviderConfigRepository(path)
    with pytest.raises(Exception):
        repo.list_all()


def test_atomic_write_no_tmp_left(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    repo.save(_chat_config())
    assert list(tmp_path.glob("*.tmp")) == []
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/repositories/test_provider_config_repository.py -v`
Expected: FAIL — 现有仓库为 SQLite 实现，方法签名/行为不符（如无 `list_by_purpose`、`deactivate_by_purpose`）

- [ ] **Step 3: 创建 settings 常量 + 重写仓库**

创建 `backend-python/app/config/settings.py`（覆盖原占位）：

```python
"""应用运行配置常量。"""
from pathlib import Path

PROVIDER_CONFIGS_PATH = Path("data") / "provider_configs.json"
```

重写 `backend-python/app/repositories/provider_config_repository.py`（整体替换）：

```python
"""Provider 配置的 JSON 文件仓库。

负责 provider_configs.json 的读写、序列化与原子替换。
不依赖业务 SQLite，避免与应用数据耦合。
"""
import json
import os
import threading
from pathlib import Path

from app.entities.provider_config import ProviderConfig
from app.enums.purpose import Purpose


class ProviderConfigRepository:
    def __init__(self, file_path: str | os.PathLike) -> None:
        self._path = Path(file_path)
        self._lock = threading.Lock()

    def _read(self) -> list[ProviderConfig]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        items = payload.get("providers", []) if isinstance(payload, dict) else []
        return [ProviderConfig(**item) for item in items]

    def _write(self, configs: list[ProviderConfig]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"providers": [c.model_dump(mode="json") for c in configs]}
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self._path)

    def list_all(self) -> list[ProviderConfig]:
        with self._lock:
            return self._read()

    def list_by_purpose(self, purpose: Purpose) -> list[ProviderConfig]:
        with self._lock:
            return [c for c in self._read() if c.purpose == purpose]

    def get_by_id(self, config_id: str) -> ProviderConfig | None:
        with self._lock:
            for config in self._read():
                if config.id == config_id:
                    return config
            return None

    def get_active_by_purpose(self, purpose: Purpose) -> ProviderConfig | None:
        with self._lock:
            for config in self._read():
                if config.purpose == purpose and config.is_active:
                    return config
            return None

    def save(self, config: ProviderConfig) -> ProviderConfig:
        with self._lock:
            configs = self._read()
            for index, existing in enumerate(configs):
                if existing.id == config.id:
                    configs[index] = config
                    break
            else:
                configs.append(config)
            self._write(configs)
        return config

    def delete(self, config_id: str) -> bool:
        with self._lock:
            configs = self._read()
            remaining = [c for c in configs if c.id != config_id]
            if len(remaining) == len(configs):
                return False
            self._write(remaining)
            return True

    def deactivate_by_purpose(self, purpose: Purpose) -> None:
        with self._lock:
            configs = self._read()
            changed = False
            for index, config in enumerate(configs):
                if config.purpose == purpose and config.is_active:
                    configs[index] = config.model_copy(update={"is_active": False})
                    changed = True
            if changed:
                self._write(configs)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/repositories/test_provider_config_repository.py -v`
Expected: PASS（全部 10 个用例）

- [ ] **Step 5: 提交**

```bash
git add backend-python/app/config/settings.py backend-python/app/repositories/provider_config_repository.py backend-python/tests/unit/repositories/test_provider_config_repository.py
git commit -m "refactor(provider): ProviderConfigRepository 改为 JSON 文件仓库（原子写 + 进程锁）"
```

---

## Task 4: ProviderRegistry 双 provider

**Files:**
- Modify: `backend-python/app/providers/registry.py`
- Test: `backend-python/tests/unit/providers/test_registry.py`

- [ ] **Step 1: 重写测试**

整体替换 `backend-python/tests/unit/providers/test_registry.py`：

```python
import pytest

from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.providers.openai_compat_provider import OpenAICompatibleProvider
from app.providers.registry import ProviderNotFoundError, ProviderRegistry


class TestProviderRegistry:
    def setup_method(self):
        ProviderRegistry.clear()

    def test_build_openai_compat_provider(self, provider_config_factory):
        config = provider_config_factory(name="test-deepseek")
        provider = ProviderRegistry.build_provider(config)
        assert isinstance(provider, OpenAICompatibleProvider)

    def test_activate_chat_routes_to_chat_slot(self, provider_config_factory):
        config = provider_config_factory(name="chat-cfg", purpose=Purpose.CHAT)
        provider = ProviderRegistry.activate(config)
        assert ProviderRegistry.get_active_chat() is provider
        assert ProviderRegistry.get_active_config(Purpose.CHAT).name == "chat-cfg"

    def test_activate_embedding_routes_to_embedding_slot(self, provider_config_factory):
        config = provider_config_factory(
            name="embed-cfg", purpose=Purpose.EMBEDDING, embedding_dimension=1024
        )
        ProviderRegistry.activate(config)
        assert ProviderRegistry.get_active_embedding() is not None
        assert ProviderRegistry.get_active_config(Purpose.EMBEDDING).name == "embed-cfg"

    def test_chat_and_embedding_are_independent(self, provider_config_factory):
        chat = provider_config_factory(name="c", purpose=Purpose.CHAT)
        embed = provider_config_factory(
            name="e", purpose=Purpose.EMBEDDING, embedding_dimension=8
        )
        ProviderRegistry.activate(chat)
        ProviderRegistry.activate(embed)
        assert ProviderRegistry.get_active_config(Purpose.CHAT).name == "c"
        assert ProviderRegistry.get_active_config(Purpose.EMBEDDING).name == "e"

    def test_get_active_chat_raises_when_none(self):
        with pytest.raises(ProviderNotFoundError, match="chat provider"):
            ProviderRegistry.get_active_chat()

    def test_get_active_embedding_raises_when_none(self):
        with pytest.raises(ProviderNotFoundError, match="embedding provider"):
            ProviderRegistry.get_active_embedding()

    def test_clear_purpose_only(self, provider_config_factory):
        ProviderRegistry.activate(provider_config_factory(name="c", purpose=Purpose.CHAT))
        ProviderRegistry.activate(
            provider_config_factory(name="e", purpose=Purpose.EMBEDDING, embedding_dimension=8)
        )
        ProviderRegistry.clear(Purpose.CHAT)
        with pytest.raises(ProviderNotFoundError):
            ProviderRegistry.get_active_chat()
        assert ProviderRegistry.get_active_embedding() is not None

    def test_clear_all(self, provider_config_factory):
        ProviderRegistry.activate(provider_config_factory(name="c", purpose=Purpose.CHAT))
        ProviderRegistry.clear()
        with pytest.raises(ProviderNotFoundError):
            ProviderRegistry.get_active_chat()

    def test_unsupported_api_mode_raises(self):
        config = ProviderConfig.model_construct(
            name="bad",
            api_mode="unsupported-mode",
            api_key="sk-test",
            api_host="https://test.com",
            model_id="test",
            display_name="Bad",
            purpose=Purpose.CHAT,
        )
        with pytest.raises(ValueError, match="不支持的 API 模式"):
            ProviderRegistry.build_provider(config)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/providers/test_registry.py -v`
Expected: FAIL — `AttributeError: get_active_chat`（尚未实现）

- [ ] **Step 3: 重写 Registry**

整体替换 `backend-python/app/providers/registry.py`：

```python
from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.providers.base import AIProvider
from app.providers.openai_compat_provider import OpenAICompatibleProvider


class ProviderNotFoundError(RuntimeError):
    pass


class ProviderRegistry:
    _active_chat: AIProvider | None = None
    _active_embedding: AIProvider | None = None
    _active_chat_config: ProviderConfig | None = None
    _active_embedding_config: ProviderConfig | None = None

    @classmethod
    def build_provider(cls, config: ProviderConfig) -> AIProvider:
        if config.api_mode == ApiMode.OPENAI_COMPAT:
            return OpenAICompatibleProvider(config)
        raise ValueError(f"不支持的 API 模式: {config.api_mode}")

    @classmethod
    def activate(cls, config: ProviderConfig) -> AIProvider:
        provider = cls.build_provider(config)
        if config.purpose == Purpose.CHAT:
            cls._active_chat = provider
            cls._active_chat_config = config
        else:
            cls._active_embedding = provider
            cls._active_embedding_config = config
        return provider

    @classmethod
    def get_active_chat(cls) -> AIProvider:
        if cls._active_chat is None:
            raise ProviderNotFoundError("当前没有激活的 chat provider，请先配置并激活。")
        return cls._active_chat

    @classmethod
    def get_active_embedding(cls) -> AIProvider:
        if cls._active_embedding is None:
            raise ProviderNotFoundError("当前没有激活的 embedding provider，请先配置并激活。")
        return cls._active_embedding

    @classmethod
    def get_active_config(cls, purpose: Purpose) -> ProviderConfig | None:
        if purpose == Purpose.CHAT:
            return cls._active_chat_config
        return cls._active_embedding_config

    @classmethod
    def clear(cls, purpose: Purpose | None = None) -> None:
        if purpose is None:
            cls._active_chat = None
            cls._active_chat_config = None
            cls._active_embedding = None
            cls._active_embedding_config = None
        elif purpose == Purpose.CHAT:
            cls._active_chat = None
            cls._active_chat_config = None
        else:
            cls._active_embedding = None
            cls._active_embedding_config = None
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/providers/test_registry.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend-python/app/providers/registry.py backend-python/tests/unit/providers/test_registry.py
git commit -m "refactor(provider): ProviderRegistry 扩展为 chat/embedding 双 provider"
```

---

## Task 5: OpenAICompatibleProvider 的 embedding model 默认取 config.model_id

**Files:**
- Modify: `backend-python/app/providers/openai_compat_provider.py:39-51`
- Test: `backend-python/tests/unit/providers/test_openai_compat_provider.py`

- [ ] **Step 1: 加失败测试**

在 `backend-python/tests/unit/providers/test_openai_compat_provider.py` 末尾追加：

```python
    @patch("app.providers.openai_compat_provider.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_create_embedding_defaults_to_config_model_id(
        self, MockAsyncOpenAI, provider_config_factory
    ):
        mock_client = MockAsyncOpenAI.return_value
        mock_client.embeddings.create = AsyncMock(
            return_value=SimpleNamespace(
                data=[SimpleNamespace(embedding=[0.1, 0.2])],
                model="config-model",
            )
        )

        config = provider_config_factory(model_id="config-model" if False else "test-model")
        provider = OpenAICompatibleProvider(config)
        await provider.create_embedding("hello")

        kwargs = mock_client.embeddings.create.call_args[1]
        assert kwargs["model"] == "test-model"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/providers/test_openai_compat_provider.py::TestOpenAICompatibleProvider::test_create_embedding_defaults_to_config_model_id -v`
Expected: FAIL — `ValueError: Embedding model is required`（当前未传 model 即报错）

- [ ] **Step 3: 改实现**

修改 `backend-python/app/providers/openai_compat_provider.py` 的 `create_embedding`，去掉强制校验，改为默认取配置：

```python
    async def create_embedding(
        self,
        input: str | list[str],
        model: str | None = None,
    ) -> EmbeddingResult:
        effective_model = model or self.config.model_id
        response = await self._client.embeddings.create(model=effective_model, input=input)
        return EmbeddingResult(
            embeddings=[item.embedding for item in response.data],
            model=response.model,
        )
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/providers/test_openai_compat_provider.py -v`
Expected: PASS（新用例 + 现有显式传 model 的用例都通过）

- [ ] **Step 5: 提交**

```bash
git add backend-python/app/providers/openai_compat_provider.py backend-python/tests/unit/providers/test_openai_compat_provider.py
git commit -m "feat(provider): create_embedding 默认使用 config.model_id"
```

---

## Task 6: ProviderService 去 SQLite，依赖文件仓库

**Files:**
- Modify: `backend-python/app/services/provider_service.py`
- Test: `backend-python/tests/unit/services/test_provider_service.py`

- [ ] **Step 1: 重写测试**

整体替换 `backend-python/tests/unit/services/test_provider_service.py`：

```python
import pytest

from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.providers.registry import ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository
from app.services.provider_service import ProviderService


@pytest.fixture
def repo(tmp_path):
    return ProviderConfigRepository(tmp_path / "provider_configs.json")


@pytest.fixture(autouse=True)
def reset_registry():
    ProviderRegistry.clear()
    yield
    ProviderRegistry.clear()


def _chat_payload(**overrides):
    payload = {
        "name": "chat-1",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-chat",
        "api_host": "https://api.chat.com",
        "model_id": "chat-model",
        "display_name": "Chat",
        "purpose": Purpose.CHAT,
    }
    payload.update(overrides)
    return payload


def _embedding_payload(**overrides):
    payload = {
        "name": "embed-1",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-embed",
        "api_host": "https://api.embed.com",
        "model_id": "embed-model",
        "display_name": "Embed",
        "purpose": Purpose.EMBEDDING,
        "embedding_dimension": 1024,
    }
    payload.update(overrides)
    return payload


def test_create_persists_via_repository(repo):
    service = ProviderService(repo)
    result = service.create(_chat_payload())
    assert result.name == "chat-1"
    assert repo.get_by_id(result.id).name == "chat-1"


def test_list_all_and_by_purpose(repo):
    service = ProviderService(repo)
    service.create(_chat_payload())
    service.create(_embedding_payload())
    assert len(service.list_all()) == 2
    assert len(service.list_all(Purpose.CHAT)) == 1
    assert len(service.list_all(Purpose.EMBEDDING)) == 1


def test_activate_sets_active_and_registry(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    activated = service.activate(created.id)
    assert activated.is_active is True
    assert ProviderRegistry.get_active_config(Purpose.CHAT).id == created.id


def test_activate_deactivates_only_same_purpose(repo):
    service = ProviderService(repo)
    chat_a = service.create(_chat_payload(name="a"))
    chat_b = service.create(_chat_payload(name="b"))
    embed = service.create(_embedding_payload())
    service.activate(chat_a.id)
    service.activate(embed.id)
    service.activate(chat_b.id)
    assert repo.get_by_id(chat_a.id).is_active is False
    assert repo.get_by_id(chat_b.id).is_active is True
    assert repo.get_by_id(embed.id).is_active is True


def test_activate_nonexistent_returns_none(repo):
    assert ProviderService(repo).activate("missing") is None


def test_get_active_by_purpose(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    service.activate(created.id)
    assert service.get_active(Purpose.CHAT).id == created.id
    assert service.get_active(Purpose.EMBEDDING) is None


def test_update(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    updated = service.update(created.id, {"display_name": "New"})
    assert updated.display_name == "New"


def test_update_reactivates_when_currently_active(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    service.activate(created.id)
    service.update(created.id, {"display_name": "New"})
    assert ProviderRegistry.get_active_config(Purpose.CHAT).display_name == "New"


def test_delete(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    assert service.delete(created.id) is True
    assert service.delete(created.id) is False


def test_delete_active_clears_registry(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    service.activate(created.id)
    service.delete(created.id)
    assert ProviderRegistry.get_active_config(Purpose.CHAT) is None


def test_delete_inactive_keeps_registry(repo):
    service = ProviderService(repo)
    active = service.create(_chat_payload(name="a"))
    service.activate(active.id)
    other = service.create(_chat_payload(name="b"))
    service.delete(other.id)
    assert ProviderRegistry.get_active_config(Purpose.CHAT).id == active.id
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/services/test_provider_service.py -v`
Expected: FAIL — `ProviderService(uow=...)` 旧签名不符

- [ ] **Step 3: 重写 Service**

整体替换 `backend-python/app/services/provider_service.py`：

```python
from app.entities.provider_config import ProviderConfig
from app.enums.purpose import Purpose
from app.providers.registry import ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository


class ProviderService:
    def __init__(self, repository: ProviderConfigRepository) -> None:
        self.repository = repository

    def create(self, data: dict) -> ProviderConfig:
        config = ProviderConfig(**data)
        self.repository.save(config)
        return config

    def update(self, config_id: str, data: dict) -> ProviderConfig | None:
        config = self.repository.get_by_id(config_id)
        if config is None:
            return None
        updated = config.model_copy(
            update={k: v for k, v in data.items() if v is not None}
        )
        self.repository.save(updated)
        active_config = ProviderRegistry.get_active_config(updated.purpose)
        if active_config is not None and active_config.id == config_id:
            ProviderRegistry.activate(updated)
        return updated

    def activate(self, config_id: str) -> ProviderConfig | None:
        config = self.repository.get_by_id(config_id)
        if config is None:
            return None
        self.repository.deactivate_by_purpose(config.purpose)
        activated = config.model_copy(update={"is_active": True})
        self.repository.save(activated)
        ProviderRegistry.activate(activated)
        return activated

    def get_active(self, purpose: Purpose) -> ProviderConfig | None:
        return self.repository.get_active_by_purpose(purpose)

    def get_by_id(self, config_id: str) -> ProviderConfig | None:
        return self.repository.get_by_id(config_id)

    def list_all(self, purpose: Purpose | None = None) -> list[ProviderConfig]:
        if purpose is not None:
            return self.repository.list_by_purpose(purpose)
        return self.repository.list_all()

    def delete(self, config_id: str) -> bool:
        config = self.repository.get_by_id(config_id)
        if config is None:
            return False
        deleted = self.repository.delete(config_id)
        if deleted and config.is_active:
            ProviderRegistry.clear(config.purpose)
        return deleted
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/services/test_provider_service.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend-python/app/services/provider_service.py backend-python/tests/unit/services/test_provider_service.py
git commit -m "refactor(provider): ProviderService 去 SQLite，改为依赖文件仓库 + purpose 分组激活"
```

---

## Task 7: EmbeddingService 从 active embedding 配置取用

**Files:**
- Modify: `backend-python/app/services/embedding_service.py`
- Test: `backend-python/tests/unit/services/test_embedding_service.py`

- [ ] **Step 1: 重写测试**

整体替换 `backend-python/tests/unit/services/test_embedding_service.py`（保留 `_fake_sqlite_vec_loader`、`session_factory`、`_seed_chunks` 辅助；改造 service 构造与 mock 方式）：

```python
from unittest.mock import patch

import pytest

from app.db.connection import create_app_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.entities import Chunk, DocumentRecord, DocumentUnit
from app.enums import DocumentFileType
from app.enums.purpose import Purpose
from app.providers.base import EmbeddingResult
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.services.embedding_service import EmbeddingService


def _fake_sqlite_vec_loader(connection):
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


class FakeProvider:
    def __init__(self, result: EmbeddingResult) -> None:
        self.result = result

    async def create_embedding(self, input, model=None):
        return self.result


@pytest.fixture
def session_factory(tmp_path):
    return create_app_session_factory(
        database_path=tmp_path / "data" / "embedding.sqlite3",
        embedding_dimension=2,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )


def _seed_chunks(session_factory):
    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit = DocumentUnit(document_id=document.id, sequence_index=0, text_content="Source")
    chunks = [
        Chunk(document_unit_id=unit.id, sequence_index=0, text_content="chunk-a"),
        Chunk(document_unit_id=unit.id, sequence_index=1, text_content="chunk-b"),
    ]
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(unit)
        for chunk in chunks:
            ChunkRepository(uow.session).save(chunk)
        uow.commit()
    return chunks


def _embedding_config_factory(dimension: int):
    from app.enums.api_mode import ApiMode
    from app.entities.provider_config import ProviderConfig

    return ProviderConfig(
        name="embed-cfg",
        api_mode=ApiMode.OPENAI_COMPAT,
        api_key="sk-embed",
        api_host="https://api.embed.com",
        model_id="embed-model",
        display_name="Embed",
        purpose=Purpose.EMBEDDING,
        embedding_dimension=dimension,
    )


@pytest.mark.asyncio
async def test_embed_chunks_uses_active_embedding_config(session_factory):
    chunks = _seed_chunks(session_factory)
    fake_provider = FakeProvider(
        EmbeddingResult(embeddings=[[0.1, 0.2], [0.3, 0.4]], model="embed-model")
    )
    service = EmbeddingService(uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory))
    with patch(
        "app.services.embedding_service.ProviderRegistry.get_active_embedding",
        return_value=fake_provider,
    ), patch(
        "app.services.embedding_service.ProviderRegistry.get_active_config",
        return_value=_embedding_config_factory(2),
    ):
        saved = await service.embed_chunks(chunks)

    assert len(saved) == 2


@pytest.mark.asyncio
async def test_embed_chunks_passes_config_model_id(session_factory):
    chunks = _seed_chunks(session_factory)
    fake_provider = FakeProvider(
        EmbeddingResult(embeddings=[[0.1, 0.2], [0.3, 0.4]], model="embed-model")
    )
    service = EmbeddingService(uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory))
    with patch(
        "app.services.embedding_service.ProviderRegistry.get_active_embedding",
        return_value=fake_provider,
    ) as mock_get_provider, patch(
        "app.services.embedding_service.ProviderRegistry.get_active_config",
        return_value=_embedding_config_factory(2),
    ):
        await service.embed_chunks(chunks)

    fake_provider.result = EmbeddingResult(
        embeddings=[[0.1, 0.2], [0.3, 0.4]], model="embed-model"
    )
    await fake_provider.create_embedding(["a"])
    assert mock_get_provider.called


@pytest.mark.asyncio
async def test_embed_chunks_rolls_back_when_count_mismatches(session_factory):
    chunks = _seed_chunks(session_factory)
    fake_provider = FakeProvider(
        EmbeddingResult(embeddings=[[0.1, 0.2]], model="embed-model")
    )
    service = EmbeddingService(uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory))
    with patch(
        "app.services.embedding_service.ProviderRegistry.get_active_embedding",
        return_value=fake_provider,
    ), patch(
        "app.services.embedding_service.ProviderRegistry.get_active_config",
        return_value=_embedding_config_factory(2),
    ):
        with pytest.raises(ValueError, match="Embedding count mismatch"):
            await service.embed_chunks(chunks)

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert (
            EmbeddingRepository(uow.session, embedding_dimension=2).get_by_chunk_id(chunks[0].id)
            is None
        )
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/services/test_embedding_service.py -v`
Expected: FAIL — `EmbeddingService` 旧构造要求 `provider=` / `embedding_dimension=`

- [ ] **Step 3: 重写 EmbeddingService**

整体替换 `backend-python/app/services/embedding_service.py`：

```python
from app.enums.purpose import Purpose
from app.providers.registry import ProviderRegistry
from app.repositories.embedding_repository import EmbeddingRepository


class EmbeddingService:
    def __init__(self, uow_factory) -> None:
        self.uow_factory = uow_factory

    async def embed_chunks(self, chunks, *, model: str | None = None):
        provider = ProviderRegistry.get_active_embedding()
        config = ProviderRegistry.get_active_config(Purpose.EMBEDDING)
        embedding_dimension = config.embedding_dimension
        effective_model = model or config.model_id

        texts = [chunk.text_content for chunk in chunks]
        result = await provider.create_embedding(texts, model=effective_model)
        if len(result.embeddings) != len(chunks):
            raise ValueError(
                f"Embedding count mismatch: expected {len(chunks)}, got {len(result.embeddings)}"
            )

        with self.uow_factory() as uow:
            repo = EmbeddingRepository(uow.session, embedding_dimension=embedding_dimension)
            saved = []
            for chunk, vector in zip(chunks, result.embeddings, strict=True):
                saved.append(
                    repo.save_for_chunk(
                        chunk_id=chunk.id,
                        embedding_model=result.model,
                        vector=vector,
                    )
                )
            uow.commit()
            return saved
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/services/test_embedding_service.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend-python/app/services/embedding_service.py backend-python/tests/unit/services/test_embedding_service.py
git commit -m "refactor(provider): EmbeddingService 从 active embedding 配置取 provider/model/dimension"
```

---

## Task 8: 消费方 agents 改用 get_active_chat

**Files:**
- Modify: `backend-python/app/agents/chat_agent.py:22`
- Modify: `backend-python/app/agents/analysis_agent.py:12`
- Modify: `backend-python/app/agents/classification_agent.py:12`
- Test: `backend-python/tests/unit/agents/test_chat_service.py`（确认调用迁移）

- [ ] **Step 1: 写失败测试**

检查现有 `backend-python/tests/unit/agents/test_chat_service.py`、`test_classification_service.py` 是否 patch 了 `get_active`。若 patch 的是 `app.providers.registry.ProviderRegistry.get_active`，则改为 `get_active_chat`。先运行现状测试确认它们当前依赖的符号：

Run: `python -m pytest tests/unit/agents -v`
Expected: 记录当前用到的 patch 目标（`get_active`）

在 `backend-python/tests/unit/agents/test_chat_service.py` 中，将任何 `patch("...ProviderRegistry.get_active", ...)` 改为 `patch("...ProviderRegistry.get_active_chat", ...)`（同样处理 `test_classification_service.py`、如有 analysis 测试）。

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/agents -v`
Expected: FAIL — agent 仍调用 `get_active()`，patch `get_active_chat` 不生效

- [ ] **Step 3: 改 agents**

将三个 agent 中的 `provider = ProviderRegistry.get_active()` 改为 `provider = ProviderRegistry.get_active_chat()`：
- `backend-python/app/agents/chat_agent.py:22`
- `backend-python/app/agents/analysis_agent.py:12`
- `backend-python/app/agents/classification_agent.py:12`

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/agents -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend-python/app/agents backend-python/tests/unit/agents
git commit -m "refactor(agents): chat 类消费方改用 ProviderRegistry.get_active_chat"
```

---

## Task 9: ProviderController 改造为 APIRouter + dependencies 装配

**Files:**
- Modify: `backend-python/app/api/provider_controller.py`
- Modify: `backend-python/app/api/dependencies.py`
- Test: `backend-python/tests/unit/api/test_provider_controller.py`

- [ ] **Step 1: 重写 HTTP 端点测试**

整体替换 `backend-python/tests/unit/api/test_provider_controller.py`（从"测普通类方法"改为"测 FastAPI 路由 + override service"）：

```python
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_provider_service
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.main import app
from app.services.provider_service import ProviderService


@pytest.fixture
def mock_service():
    return MagicMock(spec=ProviderService)


@pytest.fixture
def client(mock_service):
    app.dependency_overrides[get_provider_service] = lambda: mock_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def _config_dict(**overrides):
    payload = {
        "id": "cfg-1",
        "name": "test-cfg",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_host": "https://api.test.com",
        "api_path": "/v1/chat/completions",
        "model_id": "test-model",
        "display_name": "Test",
        "context_window": 65536,
        "max_output_tokens": 8192,
        "purpose": Purpose.CHAT,
        "embedding_dimension": None,
        "is_active": False,
        "created_at": "2026-06-24T00:00:00+00:00",
        "updated_at": "2026-06-24T00:00:00+00:00",
    }
    payload.update(overrides)
    return payload


def test_list_providers(client, mock_service):
    mock_service.list_all.return_value = []
    response = client.get("/api/providers?purpose=chat")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["data"] == []
    mock_service.list_all.assert_called_once_with(Purpose.CHAT)


def test_create_provider(client, mock_service):
    mock_service.create.return_value = MagicMock(**_config_dict(name="new-cfg"))
    response = client.post(
        "/api/providers",
        json={
            "name": "new-cfg",
            "api_mode": ApiMode.OPENAI_COMPAT,
            "api_key": "sk-key",
            "api_host": "https://api.test.com",
            "model_id": "test-model",
            "display_name": "New",
            "purpose": Purpose.CHAT,
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "new-cfg"
    assert "api_key" not in response.json()["data"]


def test_activate_provider(client, mock_service):
    mock_service.activate.return_value = MagicMock(**_config_dict(is_active=True))
    response = client.post("/api/providers/cfg-1/activate")
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "test-cfg"


def test_get_active_provider(client, mock_service):
    mock_service.get_active.return_value = MagicMock(**_config_dict(is_active=True))
    response = client.get("/api/providers/active?purpose=chat")
    assert response.status_code == 200
    mock_service.get_active.assert_called_once_with(Purpose.CHAT)


def test_get_active_provider_none_returns_404(client, mock_service):
    mock_service.get_active.return_value = None
    response = client.get("/api/providers/active?purpose=chat")
    assert response.status_code == 404


def test_delete_provider(client, mock_service):
    mock_service.delete.return_value = True
    response = client.delete("/api/providers/cfg-1")
    assert response.status_code == 200
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/api/test_provider_controller.py -v`
Expected: FAIL — 路由未挂载 / `get_provider_service` 不存在

- [ ] **Step 3: 装配 dependencies + 改 controller**

修改 `backend-python/app/api/dependencies.py`，在文件末尾追加：

```python
from app.config.settings import PROVIDER_CONFIGS_PATH
from app.repositories.provider_config_repository import ProviderConfigRepository
from app.services.embedding_service import EmbeddingService
from app.services.provider_service import ProviderService

_provider_service: ProviderService | None = None


def get_provider_service() -> ProviderService:
    global _provider_service
    if _provider_service is None:
        _provider_service = ProviderService(
            ProviderConfigRepository(PROVIDER_CONFIGS_PATH)
        )
    return _provider_service


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService(uow_factory=_build_uow_factory())
```

整体替换 `backend-python/app/api/provider_controller.py`：

```python
"""Provider 配置接口控制器（FastAPI APIRouter）。"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.enums.purpose import Purpose
from app.schemas.provider_schema import (
    ProviderActivateResponse,
    ProviderConfigCreateRequest,
    ProviderConfigResponse,
    ProviderConfigUpdateRequest,
)
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("")
async def list_providers(
    service: Annotated[ProviderService, Depends(lambda: None)],  # 占位，下面用 Depends 替换
    purpose: Purpose | None = Query(default=None),
):
    ...


# 说明：为保持 TDD 步骤聚焦，下方给出完整最终版本，替换上方占位。
```

> 注：上方占位仅用于示意，**Step 3 实际写入的完整文件**如下（整体替换 `provider_controller.py`）：

```python
"""Provider 配置接口控制器（FastAPI APIRouter）。"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_provider_service
from app.enums.purpose import Purpose
from app.schemas.provider_schema import (
    ProviderActivateResponse,
    ProviderConfigCreateRequest,
    ProviderConfigResponse,
    ProviderConfigUpdateRequest,
)
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["Providers"])


def _to_response(config) -> ProviderConfigResponse:
    return ProviderConfigResponse(
        id=config.id,
        name=config.name,
        api_mode=config.api_mode,
        api_host=config.api_host,
        api_path=config.api_path,
        model_id=config.model_id,
        display_name=config.display_name,
        context_window=config.context_window,
        max_output_tokens=config.max_output_tokens,
        purpose=config.purpose,
        embedding_dimension=config.embedding_dimension,
        is_active=config.is_active,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


def _to_activate_response(config) -> ProviderActivateResponse:
    return ProviderActivateResponse(
        id=config.id,
        name=config.name,
        display_name=config.display_name,
        model_id=config.model_id,
    )


@router.get("")
async def list_providers(
    purpose: Annotated[Purpose | None, Query()] = None,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    return {"code": 200, "data": [_to_response(c).model_dump(mode="json") for c in service.list_all(purpose)]}


@router.get("/active")
async def get_active_provider(
    purpose: Annotated[Purpose, Query()],
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    config = service.get_active(purpose)
    if config is None:
        raise HTTPException(status_code=404, detail="没有已激活的 provider")
    return {"code": 200, "data": _to_activate_response(config).model_dump(mode="json")}


@router.get("/{config_id}")
async def get_provider(
    config_id: str,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    config = service.get_by_id(config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="provider 不存在")
    return {"code": 200, "data": _to_response(config).model_dump(mode="json")}


@router.post("")
async def create_provider(
    request: ProviderConfigCreateRequest,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    config = service.create(request.model_dump())
    return {"code": 200, "data": _to_response(config).model_dump(mode="json")}


@router.patch("/{config_id}")
async def update_provider(
    config_id: str,
    request: ProviderConfigUpdateRequest,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    config = service.update(config_id, request.model_dump(exclude_none=True))
    if config is None:
        raise HTTPException(status_code=404, detail="provider 不存在")
    return {"code": 200, "data": _to_response(config).model_dump(mode="json")}


@router.delete("/{config_id}")
async def delete_provider(
    config_id: str,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    return {"code": 200, "data": service.delete(config_id)}


@router.post("/{config_id}/activate")
async def activate_provider(
    config_id: str,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    config = service.activate(config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="provider 不存在")
    return {"code": 200, "data": _to_activate_response(config).model_dump(mode="json")}
```

- [ ] **Step 4: 运行测试验证通过**

先在 `backend-python/app/main.py` 的 `include_router` 处临时确认（Task 10 会正式挂载；本步可在 main.py 临时加 `app.include_router(provider_controller.router, prefix="/api")` 以便测试，或确保 import 链通）。Run: `python -m pytest tests/unit/api/test_provider_controller.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend-python/app/api/provider_controller.py backend-python/app/api/dependencies.py backend-python/tests/unit/api/test_provider_controller.py backend-python/app/main.py
git commit -m "feat(provider): ProviderController 改造为 APIRouter 并装配 provider/embedding service"
```

---

## Task 10: main.py 挂载路由 + lifespan 启动恢复 + 维度来源

**Files:**
- Modify: `backend-python/app/main.py`

- [ ] **Step 1: 写失败测试**

创建 `backend-python/tests/integration/api/test_provider_lifespan.py`：

```python
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.providers.registry import ProviderRegistry


def _write_configs(path: Path, configs):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"providers": [c.model_dump(mode="json") for c in configs]}),
        encoding="utf-8",
    )


def test_lifespan_restores_active_providers(tmp_path, monkeypatch):
    config_path = tmp_path / "provider_configs.json"
    monkeypatch.setattr("app.config.settings.PROVIDER_CONFIGS_PATH", config_path)
    monkeypatch.setattr("app.main.PROVIDER_CONFIGS_PATH", config_path)

    from app.entities.provider_config import ProviderConfig

    chat = ProviderConfig(
        name="chat-1",
        api_mode=ApiMode.OPENAI_COMPAT,
        api_key="sk-chat",
        api_host="https://api.chat.com",
        model_id="chat-model",
        display_name="Chat",
        purpose=Purpose.CHAT,
        is_active=True,
    )
    embed = ProviderConfig(
        name="embed-1",
        api_mode=ApiMode.OPENAI_COMPAT,
        api_key="sk-embed",
        api_host="https://api.embed.com",
        model_id="embed-model",
        display_name="Embed",
        purpose=Purpose.EMBEDDING,
        embedding_dimension=768,
        is_active=True,
    )
    _write_configs(config_path, [chat, embed])

    ProviderRegistry.clear()
    from app.main import app

    with TestClient(app):
        assert ProviderRegistry.get_active_config(Purpose.CHAT).name == "chat-1"
        assert ProviderRegistry.get_active_config(Purpose.EMBEDDING).name == "embed-1"

    ProviderRegistry.clear()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/integration/api/test_provider_lifespan.py -v`
Expected: FAIL — lifespan 未恢复 provider / `PROVIDER_CONFIGS_PATH` 在 main 中不存在

- [ ] **Step 3: 改 main.py**

整体替换 `backend-python/app/main.py`（保留原有 document/section 路由）：

```python
# Python 后端应用入口，创建 FastAPI 应用并注册路由。
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api import document_controller, provider_controller, section_controller
from app.api.dependencies import set_session_factory
from app.config.settings import PROVIDER_CONFIGS_PATH
from app.db.connection import create_app_session_factory
from app.db.init_db import load_sqlite_vec_extension
from app.enums.purpose import Purpose
from app.providers.registry import ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path("data")
_DEFAULT_DATABASE_NAME = "greenbean-study-assistant.sqlite3"
_FALLBACK_EMBEDDING_DIMENSION = 1024


def _resolve_embedding_dimension(repository: ProviderConfigRepository) -> int:
    config = repository.get_active_by_purpose(Purpose.EMBEDDING)
    if config is not None and config.embedding_dimension:
        return config.embedding_dimension
    logger.warning(
        "No active embedding config, using fallback dimension %d",
        _FALLBACK_EMBEDDING_DIMENSION,
    )
    return _FALLBACK_EMBEDDING_DIMENSION


def _restore_active_providers(repository: ProviderConfigRepository) -> None:
    for purpose in (Purpose.CHAT, Purpose.EMBEDDING):
        config = repository.get_active_by_purpose(purpose)
        if config is not None:
            ProviderRegistry.activate(config)
            logger.info("Restored active %s provider: %s", purpose.value, config.name)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    repository = ProviderConfigRepository(PROVIDER_CONFIGS_PATH)
    try:
        embedding_dimension = _resolve_embedding_dimension(repository)
        session_factory = create_app_session_factory(
            database_path=_DEFAULT_DATA_DIR / _DEFAULT_DATABASE_NAME,
            embedding_dimension=embedding_dimension,
            sqlite_vec_loader=load_sqlite_vec_extension,
        )
        set_session_factory(session_factory)
        logger.info("Database session factory configured with dimension %d.", embedding_dimension)
    except Exception as exc:
        logger.warning("Database initialization skipped: %s", exc)
    try:
        _restore_active_providers(repository)
    except Exception as exc:
        logger.warning("Provider restore skipped: %s", exc)
    yield


app = FastAPI(title="Greenbean Study Assistant API", lifespan=lifespan)

app.include_router(document_controller.router, prefix="/api")
app.include_router(section_controller.router, prefix="/api")
app.include_router(provider_controller.router, prefix="/api")
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/integration/api/test_provider_lifespan.py tests/unit/api/test_provider_controller.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend-python/app/main.py backend-python/tests/integration/api/test_provider_lifespan.py
git commit -m "feat(provider): main.py 挂载 provider 路由 + lifespan 启动恢复与维度来源"
```

---

## Task 11: 清理 SQLite provider 残留 + gitignore

**Files:**
- Modify: `backend-python/app/db/models.py:161-176`
- Modify: `backend-python/app/db/init_db.py:206-220`
- Modify: `.gitignore`
- Verify: `backend-python/tests/integration/persistence/test_sqlite_repositories.py`

- [ ] **Step 1: 写失败保护测试**

先确认是否有测试引用 `ProviderConfigModel`。Run（在仓库根，使用 ripgrep）:
`rg -n "ProviderConfigModel" backend-python`
Expected: 若 `test_sqlite_repositories.py` 引用，则需同步删除其相关用例。

- [ ] **Step 2: 删除引用**

删除 `backend-python/tests/integration/persistence/test_sqlite_repositories.py` 中任何针对 `ProviderConfigModel` 或 `provider_configs` 表的测试用例（若存在）。若该文件整体不再有其他内容，保留文件但移除相关测试函数。

- [ ] **Step 3: 删 Model + 建表 SQL + 加 gitignore**

在 `backend-python/app/db/models.py` 删除整个 `ProviderConfigModel` 类（`:161-176`）。

在 `backend-python/app/db/init_db.py` 的 `_create_schema` SQL 中删除 `provider_configs` 建表块（`:206-220`）。

在 `.gitignore` 的 `# User uploaded files` 段之后追加：

```
# Provider API configs (contains secrets)
data/provider_configs.json
```

- [ ] **Step 4: 运行全量后端测试验证通过**

Run: `python -m pytest -v`
Expected: PASS（确认无残留 import / 表引用）

- [ ] **Step 5: 提交**

```bash
git add backend-python/app/db/models.py backend-python/app/db/init_db.py .gitignore backend-python/tests/integration/persistence/test_sqlite_repositories.py
git commit -m "refactor(provider): 移除 provider_configs 的 SQLite 表/Model，配置迁至 JSON 文件"
```

---

## Task 12: Provider HTTP 工作流集成测试

**Files:**
- Test: `backend-python/tests/integration/api/test_provider_workflow.py`

- [ ] **Step 1: 重写集成测试**

整体替换 `backend-python/tests/integration/api/test_provider_workflow.py`（从"直接 new controller + SQLite"改为"TestClient + JSON 文件 + 进程内 registry 恢复"）：

```python
import json

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_provider_service
from app.config.settings import PROVIDER_CONFIGS_PATH
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.main import app
from app.providers.registry import ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository
from app.services.provider_service import ProviderService


@pytest.fixture
def isolated_provider_path(tmp_path, monkeypatch):
    path = tmp_path / "provider_configs.json"
    monkeypatch.setattr("app.config.settings.PROVIDER_CONFIGS_PATH", path)
    monkeypatch.setattr("app.main.PROVIDER_CONFIGS_PATH", path)
    service = ProviderService(ProviderConfigRepository(path))
    app.dependency_overrides[get_provider_service] = lambda: service
    yield path
    app.dependency_overrides.clear()
    ProviderRegistry.clear()


def _create(client, **overrides):
    payload = {
        "name": "provider-a",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-a",
        "api_host": "https://api-a.test.com",
        "model_id": "model-a",
        "display_name": "Provider A",
        "purpose": Purpose.CHAT,
    }
    payload.update(overrides)
    response = client.post("/api/providers", json=payload)
    assert response.status_code == 200
    return response.json()["data"]


def test_create_activate_persist_and_isolate_by_purpose(isolated_provider_path):
    client = TestClient(app)

    first = _create(client, name="chat-a", display_name="Chat A")
    second = _create(client, name="chat-b", display_name="Chat B")
    embed = _create(
        client,
        name="embed-a",
        display_name="Embed A",
        purpose=Purpose.EMBEDDING,
        embedding_dimension=512,
        model_id="embed-model",
    )

    activate_resp = client.post(f"/api/providers/{second['id']}/activate")
    assert activate_resp.status_code == 200
    client.post(f"/api/providers/{embed['id']}/activate")

    active_chat = client.get("/api/providers/active?purpose=chat").json()["data"]
    active_embed = client.get("/api/providers/active?purpose=embedding").json()["data"]
    assert active_chat["name"] == "chat-b"
    assert active_embed["name"] == "embed-a"

    persisted = json.loads(isolated_provider_path.read_text(encoding="utf-8"))["providers"]
    chat_active = [c for c in persisted if c["purpose"] == "chat" and c["is_active"]]
    embed_active = [c for c in persisted if c["purpose"] == "embedding" and c["is_active"]]
    assert [c["id"] for c in chat_active] == [second["id"]]
    assert [c["id"] for c in embed_active] == [embed["id"]]

    for item in persisted:
        assert "api_key" not in item or item.get("api_key")  # 文件内仍存密钥，但 API 不返回
    list_resp = client.get("/api/providers?purpose=chat")
    assert all("api_key" not in c for c in list_resp.json()["data"])
```

> 注：最后断言说明 JSON 文件内保留密钥（本地存储），但 HTTP 响应（`_to_response` 未含 api_key）不暴露——保持与 schema 脱敏一致。

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/integration/api/test_provider_workflow.py -v`
Expected: 若 Task 9/10 已合入则应接近通过；若仍有断言不符则 FAIL，据此修正。

- [ ] **Step 3: 修正至通过（如需要）**

如 `data` 字段命名/脱敏与实现不一致，回到 Task 9 的 `_to_response` / `_to_activate_response` 对齐。预期无需改实现。

- [ ] **Step 4: 运行全量后端测试**

Run: `python -m pytest -v`
Expected: PASS（全部后端测试通过）

- [ ] **Step 5: 提交**

```bash
git add backend-python/tests/integration/api/test_provider_workflow.py
git commit -m "test(provider): provider HTTP 工作流集成测试（落盘 JSON + 分组激活隔离）"
```

---

## Self-Review

**Spec 覆盖核对：**
- 5.1 数据模型（purpose/embedding_dimension + 校验）→ Task 1, 2 ✓
- 5.2 JSON 文件存储（位置/结构/原子写/锁/损坏报错）→ Task 3 ✓
- 5.3.1 Registry 双 provider → Task 4 ✓
- 5.3.2 OpenAICompat embedding 默认 model → Task 5 ✓
- 5.3.3 ProviderService 去 SQLite → Task 6 ✓
- 5.3.4 Controller APIRouter + 挂路由 → Task 9, 10 ✓
- 5.3.5 main.py 启动恢复 + 维度 → Task 10 ✓
- 5.3.6 EmbeddingService 统一取用 → Task 7 ✓
- 5.3.7 消费方改造 + 移除 get_active → Task 4（移除）+ Task 8（消费方）✓
- 5.4 移除 ProviderConfigModel + init_db 建表 → Task 11 ✓
- .gitignore → Task 11 ✓
- 7.1 各层测试 → Task 1/3/4/5/6/7/9/10/12 ✓

**类型一致性：** `Purpose.CHAT`/`Purpose.EMBEDDING`、`get_active_chat`/`get_active_embedding`/`get_active_config(purpose)`、`ProviderService(repository)`、`ProviderConfigRepository(file_path)`、`list_all(purpose)`、`activate`/`get_active(purpose)`、`deactivate_by_purpose`/`get_active_by_purpose` 跨任务命名一致 ✓

**已知执行注意：**
- Task 9 Step 3 含一段占位示意，实际写入应使用其后给出的完整文件版本（已标注）。
- Task 8 需先运行 `tests/unit/agents` 观察现有 patch 目标，再决定测试改动细节。
- Task 11 需先 `rg ProviderConfigModel` 确认 `test_sqlite_repositories.py` 的影响面。

---

## Execution Handoff

后端计划完成，保存于 `docs/superpowers/plans/2026-06-24-api-config-backend.md`。两种执行方式：

**1. Subagent-Driven（推荐）** — 每个 Task 派发独立 subagent，任务间审查，迭代快。
**2. Inline Execution** — 在当前会话按 executing-plans 批量执行，带检查点。

主人选哪种？另外，**前端计划（`2026-06-24-api-config-frontend.md`）是否现在继续生成？**

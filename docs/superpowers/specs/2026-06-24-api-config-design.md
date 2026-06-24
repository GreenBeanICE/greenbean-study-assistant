# API 配置（云端模型 Provider 配置体系）设计

- 日期：2026-06-24
- 状态：待审阅
- 主题：打通"前端设置页 → JSON 配置 → Registry 双 provider → chat / embedding 消费"全链路
- 关联模块：`backend-python/app/{providers,services,api,repositories,entities,agents}`、`src/features/settings`、`src/App.tsx`

## 1. 背景与目标

项目要接入远程云端 API 来提供两类模型能力：

- **chat / LLM**：对话、分析、分类等文本生成（`chat_agent`、`analysis_agent`、`classification_agent` 消费）。
- **embedding**：文档切块的向量化（`EmbeddingService` 消费，供后续 RAG 检索）。

现实中这两类几乎总是不同模型，甚至不同厂商（如 chat 走 DeepSeek，embedding 走硅基流动 bge-m3）。

现有 provider 抽象层逻辑已较完整，但把 API 配置放进业务 SQLite 会带来几个问题：

1. API 配置属于**应用设置**，不是业务数据，和文档/章节/向量入同一库会提高耦合度。
2. 启动时需要先读 provider 配置再决定 embedding 维度，而 SQLite 初始化本身又依赖该维度，顺序容易打架。
3. 后续若迁移到 Tauri 安全存储或系统凭据库，SQLite 持久化会成为中间层负担。

本设计的目标是：

1. 让 chat 与 embedding **各自独立配置、各自激活**，可分别指向不同厂商。
2. 把 provider 配置从业务 SQLite **拆出到 JSON 配置文件**，降低耦合。
3. 把 `ProviderController` **挂到 FastAPI 路由**，真正对外可用。
4. 提供**前端设置页**完成配置的增删改查与激活，并支持**首启引导**。
5. 解决重启丢激活态、embedding 维度硬编码等问题。

## 2. 现状分析

### 2.1 已有（可直接复用）

- `AIProvider` 抽象基类：`chat_completion` + `create_embedding`。`providers/base.py:15`
- `OpenAICompatibleProvider`：基于 `openai.AsyncOpenAI`，chat 与 embedding 均已实现。`providers/openai_compat_provider.py:7`
- `ProviderConfig` 实体：已具备基础配置字段，适合继续作为领域模型。`entities/provider_config.py:9`
- `ProviderService`：完整 CRUD + `activate` 业务语义已具雏形。`services/provider_service.py:7`
- `ProviderController`：list/get/create/update/delete/activate/get_active 方法齐全，schema 已脱敏（Response 不含 `api_key`）。`api/provider_controller.py:10`
- `ProviderRegistry`：进程内单例 active provider。`providers/registry.py:11`
- `EmbeddingService`：已实现 `embed_chunks`，但 provider 为**构造注入**、`model` 为**调用方必传**。`services/embedding_service.py:4`
- 测试：`tests/unit/providers/test_openai_compat_provider.py`、`test_registry.py`、`tests/unit/services/test_provider_service.py`、`tests/unit/api/test_provider_controller.py`、`tests/integration/api/test_provider_workflow.py`。

### 2.2 缺口（本设计要解决的）

| # | 缺口 | 位置 |
|---|---|---|
| G1 | 一份 `ProviderConfig` 只有一个 `model_id`，仅服务 chat；embedding 无独立配置入口 | `entities/provider_config.py` |
| G2 | `ProviderController` 未挂 FastAPI 路由（普通类，集成测试直接 new 调用） | `app/main.py:37` |
| G3 | `ProviderRegistry` 是进程内单例，重启即丢；缺少持久化恢复 | `providers/registry.py:11` |
| G4 | `embedding_dimension` 硬编码为 `8`（测试占位） | `app/main.py:17` |
| G5 | `dependencies.py` 未装配 `provider_service` / `embedding_service` | `api/dependencies.py` |
| G6 | `EmbeddingService` 与 chat 侧取用 provider 的方式不一致（注入 vs `registry.get_active()`） | `services/embedding_service.py:5` |
| G7 | provider 配置当前建模在 SQLite 方向，和业务库耦合过高 | `db/models.py:161`、`db/init_db.py:206` |
| G8 | 前端无 `settings` feature，`chatApi.ts` 等为空占位 | `src/features/` |

## 3. 范围

### 3.1 本次做

- 数据模型：`ProviderConfig` 增加 `purpose` + `embedding_dimension` 字段。
- 存储：新增 `data/provider_configs.json` 作为 provider 配置持久化文件，支持多套配置与分组激活。
- 后端运行时：`ProviderRegistry` 双 provider；文件仓库 / service / controller 按 purpose 扩展；`ProviderController` 改造为 FastAPI `APIRouter` 并挂载；`main.py` 启动恢复 + embedding 维度来源；`dependencies.py` 装配 provider/embedding service；消费方统一取用方式。
- 前端：新建 `src/features/settings`（`providerApi`、`types`、设置页、列表/表单组件）；`App.tsx` 视图切换；首启引导。
- 测试：同步更新受影响的 unit/integration 测试，新增 controller HTTP 端点测试与前端组件测试。
- 忽略规则：把本地配置文件加入 git ignore，避免把 API 密钥提交到仓库。

### 3.2 本次不做（后续任务）

- Tauri 自动拉起 Python 后端（`src-tauri/src/services/python_backend_service.rs` 仍为占位）；开发期手动 `uvicorn app.main:app`。
- `vector_index_builder` 等真正切块入库的 RAG 流程（见 `2026-06-24-构建-pageindex-和-rag-design.md`）；本设计只保证 embedding 配置可被消费、维度正确。
- 重排（reranker）模型配置。
- API 密钥加密（YAGNI，JSON 明文存本地文件；后续可迁移到系统安全存储）。
- 多用户 / 多工作区级配置（当前为应用级单用户）。
- 配置文件热更新监听；本期仅保证通过 API 修改后进程内状态立即同步。

## 4. 设计决策

| 决策 | 选择 | 理由 |
|---|---|---|
| D1 存储方式 | 使用 `data/provider_configs.json` | 降低和业务 SQLite 的耦合；实现简单；后续可平滑迁移到更安全存储 |
| D2 chat / embedding 关系 | 两套完全独立配置，可不同厂商/host/key | 贴合现实多厂商混用 |
| D3 每类套数 | 两类都可存多套，`purpose` 分组内 `is_active` 唯一 | 可保存多个备选随时切换；激活互不跨组影响 |
| D4 写入方式 | 仓库全量读写 JSON，使用临时文件 + 原子替换 | 避免半写入损坏文件，满足桌面单用户场景 |
| D5 前端入口 | 独立设置页 + 首启引导 | 配置项较多，独立页清晰；缺配置时引导 |
| D6 前端依赖 | 不引入 react-router / 表单库 | 用视图状态切换 + 原生表单 + tailwind，贴合现有自研风格 |

## 5. 详细设计

### 5.1 数据模型

`ProviderConfig` 实体新增两列：

- `purpose: Literal["chat", "embedding"]`（必填，区分用途）
- `embedding_dimension: int | None`（仅 embedding 用，chat 配置为 `None`）

其余字段（`name`/`api_mode`/`api_key`/`api_host`/`api_path`/`model_id`/`display_name`/`context_window`/`max_output_tokens`/`is_active`/时间戳）不变。

涉及文件：

- `entities/provider_config.py`：加两个字段与校验（`purpose="embedding"` 时 `embedding_dimension` 必须为正整数；`purpose="chat"` 时必须为 `None`）。
- `schemas/provider_schema.py`：Create/Update/Response 增加对应字段；Create 中 `purpose` 必填，`embedding_dimension` 按 purpose 条件必填。
- `enums/`：新增 `Purpose` 枚举（`"chat"` / `"embedding"`），避免散落字面量（SonarQube）。

### 5.2 配置文件存储

#### 5.2.1 文件位置与结构

- 文件路径：`data/provider_configs.json`
- 首次不存在时自动创建为：

```json
{
  "providers": []
}
```

- 文件只存 provider 配置，不存业务数据。
- `.gitignore` 新增 `data/provider_configs.json`，避免明文密钥被提交。

#### 5.2.2 `ProviderConfigRepository` 改为文件仓库

保留仓库名与模块路径，降低上层改动：`repositories/provider_config_repository.py`

职责：

- 读取 `provider_configs.json`
- 反序列化 / 序列化 `ProviderConfig`
- 提供 `list_all()`、`list_by_purpose(purpose)`、`get_by_id(id)`、`get_active_by_purpose(purpose)`、`save(config)`、`delete(id)`、`deactivate_by_purpose(purpose)`

实现约束：

- 每次写入先写临时文件，再原子替换原文件。
- 仓库内部使用进程级锁，防止并发请求把 JSON 写乱。
- 文件损坏或 JSON 非法时抛清晰异常，由 API 层转成 500，避免静默覆盖坏数据。

### 5.3 后端运行时

#### 5.3.1 `ProviderRegistry` 双 provider

- 由单一 `_active_provider` 扩展为分别持有 `_active_chat` 与 `_active_embedding`。
- `activate(config)`：按 `config.purpose` 路由到对应槽位。
- 新增 `get_active_chat()` / `get_active_embedding()` / `get_active_config(purpose)`。
- `clear()` 清空两者；`clear(purpose)` 清空指定用途。
- 维持现有“未激活时抛 `ProviderNotFoundError`”语义，分用途各自判断。

#### 5.3.2 `OpenAICompatibleProvider` 微调

- `create_embedding` 的 `model` 默认取 `self.config.model_id`（embedding 配置的 `model_id` 即 embedding 模型），不再强制调用方传 model；显式传参仍可覆盖。
- chat 侧继续用 `config.model_id`。
- 统一“配置即模型”，消费方无需关心模型名。

#### 5.3.3 `ProviderService` 去 SQLite 化

- `ProviderService` 改为依赖文件仓库，不再依赖 `SqlAlchemyUnitOfWork`。
- `list_all(purpose=None)`、`get_active(purpose)`、`activate(config_id)` 内部按 config 的 purpose 调用 `deactivate_by_purpose`。
- `create` / `update` 透传 `purpose` / `embedding_dimension`。
- 激活成功后同步更新 `ProviderRegistry`，删除激活项时同步清空对应 purpose。

#### 5.3.4 `ProviderController` 改造为 `APIRouter`

参照 `document_controller.py:21` 的模式（`APIRouter` + `Depends` + 统一 `{"code":200,"data":...}` 响应）：

- 路由：
  - `GET /api/providers?purpose=chat|embedding` —— 列表（脱敏）
  - `POST /api/providers` —— 新增（body 含 `purpose`）
  - `GET /api/providers/{id}` —— 详情（脱敏）
  - `PATCH /api/providers/{id}` —— 更新
  - `DELETE /api/providers/{id}` —— 删除
  - `POST /api/providers/{id}/activate` —— 激活（仅影响同 purpose 分组）
  - `GET /api/providers/active?purpose=chat|embedding` —— 当前激活
- `api/dependencies.py` 新增 `get_provider_service()`（供 router `Depends` 注入）。
- `app/main.py` 增加 `app.include_router(provider_controller.router, prefix="/api")`。
- `tests/unit/api/test_provider_controller.py` 迁移为 HTTP 端点测试（参照 `tests/integration/api/test_document_controller.py` 的 `TestClient` 模式）。
- `tests/integration/api/test_provider_workflow.py` 改为文件持久化工作流测试（去除对 `ProviderController` 类的直接依赖与 SQLite 假设）。
- service 层逻辑测试（`tests/unit/services/test_provider_service.py`）保留。

#### 5.3.5 `main.py` 启动恢复 + 维度来源

- 启动时先初始化业务 SQLite（不再包含 provider 配置表职责）。
- `initialize_database(..., embedding_dimension=...)` 在本期仅承担 app-level 默认 / 兜底维度来源，并同步写入 `app_metadata`；不再承载 provider 配置恢复职责。
- 然后读取 `provider_configs.json` 中 active 的 chat config 与 embedding config，分别 `ProviderRegistry.activate(...)`，解决 G3。
- embedding 维度：优先取 active embedding 配置的 `embedding_dimension`，移除 `main.py` 中硬编码 `8`（G4）；无 active embedding 配置时记日志并使用一个保守默认值（如 `1024`）。
- 该运行时维度由 `EmbeddingService` 传给 `EmbeddingRepository` 做向量长度校验与持久化，避免调用方手工传递维度。

#### 5.3.6 `EmbeddingService` 统一取用方式

- 改为内部通过 `ProviderRegistry.get_active_embedding()` 获取 provider；`model` 默认取该配置的 `model_id`；`embedding_dimension` 取该配置的 `embedding_dimension`（G6）。
- `dependencies.py` 新增 `get_embedding_service()` 装配（不再要求外部注入 provider/model/dimension）。
- `embed_chunks` 保留显式传 `model` 覆盖能力，但默认从 active 配置取。

#### 5.3.7 消费方改造

- `agents/chat_agent.py:22`、`agents/analysis_agent.py:12`、`agents/classification_agent.py:12` 的 `ProviderRegistry.get_active()` → `get_active_chat()`。
- 移除现有 `ProviderRegistry.get_active()`（双 provider 后单 active 语义不再成立，保留会引入歧义）；所有调用方迁移到 `get_active_chat()` / `get_active_embedding()`。

### 5.4 数据库初始化边界

- `db/models.py` 移除 `ProviderConfigModel`。
- `db/init_db.py` 移除 `provider_configs` 表建表逻辑。
- `app_metadata` 若仍仅服务向量层保留；provider 配置不再进入业务数据库。
- 业务 SQLite 只承担文档、章节、切块、向量、分析、聊天等业务数据持久化。

### 5.5 前端

#### 5.5.1 视图切换（无新依赖）

`src/App.tsx` 现有 `useState(showSplash)` + `AnimatePresence` 切换 splash/workspace，扩展为：

```
view: 'splash' | 'workspace' | 'settings'
```

- 入口：`WorkspacePage` 顶栏新增齿轮图标 → `setView('settings')`。
- `SettingsPage` 顶栏“返回”按钮 → `setView('workspace')`。

#### 5.5.2 新 feature `src/features/settings/`

```
settings/
├─ api/providerApi.ts     # 复用 src/lib/apiClient.request 封装
├─ types.ts               # ProviderConfig / ProviderPayload / Purpose
├─ pages/SettingsPage.tsx # 设置页主容器
└─ components/
    ├─ PurposeSection.tsx # chat / embedding 分区（标题 + 新增按钮 + 列表）
    ├─ ProviderList.tsx   # 配置列表（激活态 + 设为激活 / 编辑 / 删除）
    └─ ProviderForm.tsx   # 新增 / 编辑表单（Modal）
```

`providerApi.ts` 方法（参照 `document/api/documentApi.ts`）：

- `listProviders(purpose)` → `GET /providers?purpose=`
- `createProvider(payload)` → `POST /providers`
- `updateProvider(id, payload)` → `PATCH /providers/{id}`
- `deleteProvider(id)` → `DELETE /providers/{id}`
- `activateProvider(id)` → `POST /providers/{id}/activate`
- `getActiveProvider(purpose)` → `GET /providers/active?purpose=`

#### 5.5.3 设置页 UI

```
模型设置                              [返回工作区]
┌─ 聊天模型 (chat) ────────────────────── [+ 新增] ┐
│  DeepSeek对话 | deepseek-chat | ●已激活 [设为激活][编辑][删除]
│  通义千问      | qwen-plus    | ○       [设为激活][编辑][删除]
├─ 向量模型 (embedding) ──────────────── [+ 新增] ┤
│  硅基bge-m3 | BAAI/bge-m3 | ●已激活 [设为激活][编辑][删除]
└────────────────────────────────────────────────┘
```

- 激活：同 purpose 内单选；点“设为激活”→ `activateProvider` → 刷新该分区列表。
- `ProviderForm` 字段：`name`、`display_name`、`api_mode`（默认 `openai-compat`，下拉）、`api_host`、`api_key`（password 输入）、`model_id`、`context_window`、`max_output_tokens`；**embedding 区额外 `embedding_dimension`**。
- 列表项不展示 `api_key`（后端 Response 已脱敏）。
- embedding 区显示一条轻提示：“切换向量模型后，已有索引可能需要重建。”

#### 5.5.4 首启引导

- splash 结束、进入 workspace 前，并行调用 `getActiveProvider('chat')` 与 `getActiveProvider('embedding')`。
- 任一缺失 → 弹引导 Modal“尚未配置 聊天 / 向量 模型，是否前往设置？”→ 确认跳 `SettingsPage`。
- 仅在缺失时弹；用户可关闭 Modal 暂不配置（功能调用时会因无 active provider 报错并提示去配置）。

### 5.6 通信

- 完全复用 `src/lib/apiClient.ts`：相对路径 `/api/...`，开发期 vite proxy 转发到 `http://localhost:8000`（`vite.config.ts:34`）。
- 开发期手动启动后端：`cd backend-python && uvicorn app.main:app --reload --port 8000`。
- 生产期 Tauri 桥接 `/api` 留后续任务（见 3.2）。

## 6. 数据流

**启动恢复**

```
lifespan → 初始化业务 SQLite（使用默认/兜底维度写入 app_metadata）
         → 读取 provider_configs.json
         → 读 active chat config → registry.activate(chat)
         → 读 active embedding config → registry.activate(embedding)
         → 运行时取 embedding.embedding_dimension → EmbeddingService/EmbeddingRepository 使用
```

**新增并激活 chat 配置**

```
SettingsPage 表单 → providerApi.createProvider(purpose=chat)
                  → providerApi.activateProvider(id)
                  → service.activate
                  → repository.deactivate_by_purpose(chat) + save(config)
                  → registry.activate(chat config)
```

**chat 调用**

```
chat_agent → registry.get_active_chat() → provider.chat_completion(model 自动=chat config.model_id)
```

**embedding 调用**

```
EmbeddingService → registry.get_active_embedding() → provider.create_embedding(model 默认=embedding config.model_id)
                 → 按 embedding config.embedding_dimension 存向量
```

## 7. 测试策略

### 7.1 后端 Python（pytest）

- `tests/unit/entities/test_entities.py`：新增 `ProviderConfig` 对 `purpose` / `embedding_dimension` 的校验用例（chat 不允许带 dimension、embedding 必须带正整数 dimension）。
- `tests/unit/providers/test_registry.py`：覆盖双 provider（`get_active_chat` / `get_active_embedding`、分组 `activate` / `clear(purpose)`）。
- `tests/unit/providers/test_openai_compat_provider.py`：`create_embedding` 默认取 `config.model_id`。
- `tests/unit/repositories/test_provider_config_repository.py`：覆盖 JSON 文件仓库的 list/get/save/delete/activate、空文件初始化、损坏文件报错、原子写入基本行为。
- `tests/unit/services/test_provider_service.py`：按 purpose 的 list / activate / 分组互不影响。
- `tests/unit/services/test_embedding_service.py`：从 active embedding 配置取 provider/model/dimension。
- `tests/integration/api/test_provider_controller.py`：用 `TestClient` 覆盖 HTTP 端点（CRUD + activate + active，含 purpose 维度与脱敏）。
- `tests/integration/api/test_provider_workflow.py`：覆盖“create→activate→落盘 JSON→进程重启后恢复→分组隔离”。
- 新增 lifespan 启动恢复的 integration 测试（重启后 active 配置自动激活、维度正确）。

### 7.2 前端（Vitest + Testing Library）

- `providerApi.test.ts`：各方法正确拼路径、传 body、解析 `{code,data}`。
- `SettingsPage.test.tsx` / `ProviderList.test.tsx` / `ProviderForm.test.tsx`：渲染、激活交互、表单提交、embedding 区多渲染 `embedding_dimension` 字段。
- 首启引导逻辑测试：缺 chat / 缺 embedding / 两者齐全的分支。
- `App.tsx` 视图切换测试。

### 7.3 SonarQube

- `purpose` 值用 `Purpose` 枚举，避免重复字面量。
- controller 改造后不留与 service 重复的逻辑层。
- 文件仓库的读写辅助逻辑抽成私有方法，避免重复代码。

## 8. 风险与取舍

- **密钥仍是明文**：只是从 SQLite 明文变成 JSON 明文；本期接受，后续可迁移到系统安全存储。
- **文件并发写入**：桌面单用户场景风险可控，但仍需做进程内锁 + 原子替换，避免并发请求损坏配置文件。
- **现有测试迁移成本**：原本围绕 SQLite provider repository 的持久化测试要迁移到文件仓库测试；换取更清晰的边界，值得。
- **embedding 切换导致维度变化**：前端给“切换模型可能需要重建索引”提示；本设计不做自动重建。
- **`get_active()` 移除**：双 provider 后移除旧 `get_active()`，所有调用方迁移；不保留兼容层以避免歧义。

## 9. 验收标准

1. 前端设置页可对 chat 与 embedding 分别新增 / 编辑 / 删除配置，并各自激活一套；同 purpose 内激活唯一，跨 purpose 互不影响。
2. 后端 `GET /api/providers/active?purpose=chat|embedding` 返回正确激活项；Response 不含 `api_key`。
3. `data/provider_configs.json` 不存在时自动创建为空结构；存在时能正确恢复已激活配置。
4. 重启 Python 后端后，激活态自动恢复，`registry.get_active_chat()` / `get_active_embedding()` 可用。
5. `chat_agent` 等使用激活的 chat 配置发起请求；`EmbeddingService` 使用激活的 embedding 配置的 `model_id` 与 `embedding_dimension`。
6. 首启缺配置时前端弹引导；引导可跳转设置页。
7. `npm run test:frontend`、`npm run test:python` 全部通过；SonarQube 无新增问题。

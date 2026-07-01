"""Embedding Provider 配置。"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, SecretStr

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EMBEDDING_PROVIDERS_SECRETS_PATH = (
    BACKEND_ROOT / "secrets" / "embedding_providers.json"
)
DEFAULT_EMBEDDING_SECRETS_PATH = BACKEND_ROOT / "secrets" / "embedding.json"
SUPPORTED_EMBEDDING_API_MODE = "google"


class EmbeddingSettingsError(RuntimeError):
    """Embedding 密钥配置无法安全加载。"""


class GoogleEmbeddingSettings(BaseModel):
    """Google Embedding API 配置。"""

    api_key: SecretStr
    model_id: str = "gemini-embedding-001"
    output_dimension: int = Field(default=768, gt=0)
    batch_size: int = Field(default=16, gt=0)


def load_google_embedding_settings(
    secrets_path: str | Path | None = None,
) -> GoogleEmbeddingSettings:
    """从本地 JSON 密钥文件加载当前 active 的 Google Embedding 配置。

    默认优先读取新版 embedding_providers.json；不存在时兼容旧版 embedding.json。
    显式传入 secrets_path 时同时支持新版和旧版结构。
    """

    path = _resolve_embedding_secrets_path(secrets_path)
    payload = _read_json_object(path)
    if "active" in payload or "providers" in payload:
        return _settings_from_provider_payload(payload)
    return _settings_from_legacy_payload(payload)


def _resolve_embedding_secrets_path(secrets_path: str | Path | None) -> Path:
    if secrets_path is not None:
        return Path(secrets_path)
    if DEFAULT_EMBEDDING_PROVIDERS_SECRETS_PATH.exists():
        return DEFAULT_EMBEDDING_PROVIDERS_SECRETS_PATH
    return DEFAULT_EMBEDDING_SECRETS_PATH


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise EmbeddingSettingsError(f"Embedding 密钥文件不存在: {path}") from exc
    except OSError as exc:
        raise EmbeddingSettingsError(f"无法读取 Embedding 密钥文件: {path}") from exc

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise EmbeddingSettingsError("Embedding 密钥文件不是有效 JSON") from exc
    if not isinstance(payload, dict):
        raise EmbeddingSettingsError("Embedding 密钥文件顶层必须是 JSON object")
    return payload


def _settings_from_provider_payload(payload: dict[str, Any]) -> GoogleEmbeddingSettings:
    active = _required_string(payload, "active", "Embedding 密钥文件缺少 active")
    providers = payload.get("providers")
    if not isinstance(providers, dict):
        raise EmbeddingSettingsError("Embedding 密钥文件缺少 providers")

    provider_config = providers.get(active)
    if not isinstance(provider_config, dict):
        raise EmbeddingSettingsError(
            f"Embedding active 指向不存在的 provider: {active}"
        )

    api_mode = _required_string(
        provider_config,
        "api_mode",
        f"Embedding provider {active} 缺少 api_mode",
    )
    if api_mode != SUPPORTED_EMBEDDING_API_MODE:
        raise EmbeddingSettingsError(f"不支持的 Embedding api_mode: {api_mode}")

    api_key = _required_string(
        provider_config,
        "api_key",
        f"Embedding provider {active} 缺少 api_key",
    )
    model_id = _required_string(
        provider_config,
        "model_id",
        f"Embedding provider {active} 缺少 model_id",
    )
    dimension = provider_config.get("dimension")
    if not isinstance(dimension, int) or dimension <= 0:
        raise EmbeddingSettingsError(
            f"Embedding provider {active} 缺少有效的 dimension"
        )

    return GoogleEmbeddingSettings(
        api_key=api_key,
        model_id=model_id,
        output_dimension=dimension,
    )


def _settings_from_legacy_payload(payload: dict[str, Any]) -> GoogleEmbeddingSettings:
    google_config = payload.get("google") if isinstance(payload, dict) else None
    api_key = google_config.get("api_key") if isinstance(google_config, dict) else None
    if not isinstance(api_key, str) or not api_key.strip():
        raise EmbeddingSettingsError("Embedding 密钥文件缺少有效的 google.api_key")

    return GoogleEmbeddingSettings(api_key=api_key.strip())


def _required_string(payload: dict[str, Any], key: str, message: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EmbeddingSettingsError(message)
    return value.strip()

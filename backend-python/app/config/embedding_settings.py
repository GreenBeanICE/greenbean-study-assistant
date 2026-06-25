"""Embedding Provider 配置。"""

import json
from pathlib import Path

from pydantic import BaseModel, Field, SecretStr

DEFAULT_EMBEDDING_SECRETS_PATH = (
    Path(__file__).resolve().parents[2] / "secrets" / "embedding.json"
)


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
    """从本地 JSON 密钥文件加载 Google Embedding 配置。"""

    path = Path(secrets_path) if secrets_path is not None else DEFAULT_EMBEDDING_SECRETS_PATH
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

    google_config = payload.get("google") if isinstance(payload, dict) else None
    api_key = google_config.get("api_key") if isinstance(google_config, dict) else None
    if not isinstance(api_key, str) or not api_key.strip():
        raise EmbeddingSettingsError("Embedding 密钥文件缺少有效的 google.api_key")

    return GoogleEmbeddingSettings(api_key=api_key.strip())

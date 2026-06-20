"""Embedding Provider 配置。"""

from pydantic import BaseModel, Field, SecretStr


class GoogleEmbeddingSettings(BaseModel):
    """Google Embedding API 配置。"""

    api_key: SecretStr
    model_id: str = "gemini-embedding-001"
    output_dimension: int = Field(default=768, gt=0)
    batch_size: int = Field(default=16, gt=0)

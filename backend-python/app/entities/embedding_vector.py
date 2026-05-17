from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class EmbeddingVector(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="向量记录唯一 ID，使用 UUID 字符串。",
    )
    document_unit_id: str = Field(..., description="对应的内容单元 ID。")
    embedding_model: str = Field(..., description="生成向量的模型名称。")
    vector_dimension: int = Field(..., description="向量维度。")
    vector: list[float] | None = Field(
        default=None, description="逻辑向量值，持久化格式由后续数据库层决定。"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="创建时间。"
    )

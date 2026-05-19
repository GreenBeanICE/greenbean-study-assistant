from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class EmbeddingVector(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="向量记录唯一 ID。")
    document_unit_id: str = Field(..., description="关联的内容单元 ID。")
    embedding_model: str = Field(..., description="生成向量的 embedding 模型名称。")
    vector_dimension: int = Field(..., gt=0, description="向量维度，也就是 vector 中应有多少个数字。")
    vector: list[float] | None = Field(default=None, description="逻辑向量值，具体持久化格式由数据库层决定。")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间。")

    @model_validator(mode="after")
    def validate_vector_dimension(self) -> "EmbeddingVector":
        if self.vector is not None and len(self.vector) != self.vector_dimension:
            raise ValueError("向量长度必须等于 vector_dimension")
        return self

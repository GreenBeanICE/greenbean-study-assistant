from uuid import uuid4

from pydantic import BaseModel, Field


class SectionUnitLink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="关联记录唯一 ID，使用 UUID 字符串。")
    section_id: str = Field(..., description="关联的小节 ID。")
    document_unit_id: str = Field(..., description="关联的内容单元 ID。")
    order_index: int = Field(..., description="内容单元在该小节中的顺序。")

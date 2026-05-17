from uuid import uuid4

from pydantic import BaseModel, Field


class SectionUnitLink(BaseModel):
    """连接小节和内容单元；数据库层应保证同一小节内的关联和排序唯一。"""

    id: str = Field(default_factory=lambda: str(uuid4()), description="关联记录唯一 ID。")
    section_id: str = Field(..., description="关联的小节 ID。")
    document_unit_id: str = Field(
        ...,
        description="关联的内容单元 ID；持久化层应保证同一小节内不重复关联。",
    )
    order_index: int = Field(
        ...,
        description="内容单元在该小节中的顺序；持久化层应保证同一小节内唯一。",
    )

from __future__ import annotations

from pydantic import BaseModel, Field

from app.entities import DocumentUnit, Section
from app.services.section_service import SectionTreeNode


class SectionSummary(BaseModel):
    id: str
    document_id: str
    title: str
    level: int
    order_index: int
    start_page: int | None
    end_page: int | None

    @classmethod
    def from_entity(cls, section: Section) -> "SectionSummary":
        return cls(
            id=section.id,
            document_id=section.document_id,
            title=section.title,
            level=section.level,
            order_index=section.order_index,
            start_page=section.start_page,
            end_page=section.end_page,
        )


class SectionTreeNodeResponse(BaseModel):
    id: str
    title: str
    level: int
    order_index: int
    start_page: int | None = None
    end_page: int | None = None
    children: list["SectionTreeNodeResponse"] = Field(default_factory=list)

    @classmethod
    def from_node(cls, node: SectionTreeNode) -> "SectionTreeNodeResponse":
        return cls(
            id=node.id,
            title=node.title,
            level=node.level,
            order_index=node.order_index,
            start_page=node.start_page,
            end_page=node.end_page,
            children=[cls.from_node(child) for child in node.children],
        )


class SectionContentUnit(BaseModel):
    id: str
    sequence_index: int
    page_number: int | None
    text_content: str

    @classmethod
    def from_entity(cls, unit: DocumentUnit) -> "SectionContentUnit":
        return cls(
            id=unit.id,
            sequence_index=unit.sequence_index,
            page_number=unit.page_number,
            text_content=unit.text_content,
        )


class SectionContentResponse(BaseModel):
    anchor_unit_id: str | None = None
    units: list[SectionContentUnit] = Field(default_factory=list)

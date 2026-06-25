# 上下文构建器，用于组装 RAG 和 Agent 所需上下文。

from dataclasses import dataclass
from typing import Protocol

from app.entities import DocumentUnit, Section


class SectionNotFoundError(ValueError):
    """指定的小节不存在。"""


class SectionPageRangeMissingError(ValueError):
    """小节缺少可用于召回内容的页码范围。"""


class SectionRepositoryProtocol(Protocol):
    def get_by_id(self, section_id: str) -> Section | None:
        """按 ID 读取小节。"""


class DocumentUnitRepositoryProtocol(Protocol):
    def list_by_document_and_page_range(
        self,
        *,
        document_id: str,
        start_page: int,
        end_page: int,
    ) -> list[DocumentUnit]:
        """读取文档指定页码范围内的内容单元。"""


@dataclass(frozen=True)
class SectionContextUnit:
    """小节上下文中的单个内容单元。"""

    document_unit_id: str
    sequence_index: int
    page_number: int | None
    text_content: str
    metadata_json: dict | None


@dataclass(frozen=True)
class SectionContext:
    """小节召回上下文。"""

    section_id: str
    document_id: str
    title: str
    start_page: int
    end_page: int
    units: list[SectionContextUnit]
    context_text: str


class SectionContextBuilder:
    """按 Section 页码范围召回 DocumentUnit，并组装为分析上下文。"""

    def __init__(
        self,
        *,
        section_repository: SectionRepositoryProtocol,
        document_unit_repository: DocumentUnitRepositoryProtocol,
    ) -> None:
        self.section_repository = section_repository
        self.document_unit_repository = document_unit_repository

    def build_for_section(self, section_id: str) -> SectionContext:
        section = self.section_repository.get_by_id(section_id)
        if section is None:
            raise SectionNotFoundError(f"Section not found: {section_id}")

        start_page = section.start_page
        end_page = section.end_page
        if start_page is None or end_page is None or end_page < start_page:
            raise SectionPageRangeMissingError(
                f"Section page range is missing or invalid: {section_id}"
            )

        document_units = self.document_unit_repository.list_by_document_and_page_range(
            document_id=section.document_id,
            start_page=start_page,
            end_page=end_page,
        )
        context_units = [
            SectionContextUnit(
                document_unit_id=unit.id,
                sequence_index=unit.sequence_index,
                page_number=unit.page_number,
                text_content=unit.text_content,
                metadata_json=unit.metadata_json,
            )
            for unit in sorted(
                document_units,
                key=lambda item: item.sequence_index,
            )
        ]
        return SectionContext(
            section_id=section.id,
            document_id=section.document_id,
            title=section.title,
            start_page=start_page,
            end_page=end_page,
            units=context_units,
            context_text="\n\n".join(unit.text_content for unit in context_units),
        )

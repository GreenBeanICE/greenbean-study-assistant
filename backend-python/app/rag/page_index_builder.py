from dataclasses import dataclass
from typing import Any

from app.entities import DocumentUnit


@dataclass(frozen=True)
class PageIndexEntry:
    document_id: str
    document_unit_id: str
    page_number: int
    sequence_index: int
    text_content: str
    char_count: int
    metadata_json: dict[str, Any] | None
    parser_name: str | None
    parser_version: str | None


@dataclass(frozen=True)
class PageIndex:
    document_id: str
    pages: list[PageIndexEntry]

    @property
    def page_count(self) -> int:
        return len(self.pages)


class PageIndexBuilder:
    def build_from_document_units(
        self,
        *,
        document_id: str,
        document_units: list[DocumentUnit],
    ) -> PageIndex:
        pages = [
            PageIndexEntry(
                document_id=unit.document_id,
                document_unit_id=unit.id,
                page_number=unit.page_number,
                sequence_index=unit.sequence_index,
                text_content=unit.text_content,
                char_count=len(unit.text_content),
                metadata_json=unit.metadata_json,
                parser_name=unit.parser_name,
                parser_version=unit.parser_version,
            )
            for unit in sorted(
                document_units,
                key=lambda item: (
                    item.page_number if item.page_number is not None else 10**9,
                    item.sequence_index,
                ),
            )
            if unit.document_id == document_id and unit.page_number is not None
        ]
        return PageIndex(document_id=document_id, pages=pages)

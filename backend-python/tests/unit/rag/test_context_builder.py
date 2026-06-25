"""按章节页码范围构建上下文的测试。"""

import pytest

from app.entities import DocumentUnit, Section
from app.rag.context_builder import (
    SectionContextBuilder,
    SectionNotFoundError,
    SectionPageRangeMissingError,
)


class FakeSectionRepository:
    def __init__(self, sections: dict[str, Section]) -> None:
        self._sections = sections

    def get_by_id(self, section_id: str) -> Section | None:
        return self._sections.get(section_id)


class FakeDocumentUnitRepository:
    def __init__(self, units: list[DocumentUnit]) -> None:
        self._units = units
        self.received_query: tuple[str, int, int] | None = None

    def list_by_document_and_page_range(
        self,
        *,
        document_id: str,
        start_page: int,
        end_page: int,
    ) -> list[DocumentUnit]:
        self.received_query = (document_id, start_page, end_page)
        return [
            unit
            for unit in sorted(self._units, key=lambda item: item.sequence_index)
            if unit.document_id == document_id
            and unit.page_number is not None
            and start_page <= unit.page_number <= end_page
        ]


def _section(
    *,
    section_id: str = "section-1",
    document_id: str = "document-1",
    start_page: int | None = 2,
    end_page: int | None = 3,
) -> Section:
    return Section(
        id=section_id,
        document_id=document_id,
        title="第二章",
        level=1,
        order_index=0,
        start_page=start_page,
        end_page=end_page,
        metadata_json={"source": "page-index"},
    )


def _unit(
    *,
    unit_id: str,
    sequence_index: int,
    text_content: str,
    page_number: int,
    document_id: str = "document-1",
) -> DocumentUnit:
    return DocumentUnit(
        id=unit_id,
        document_id=document_id,
        sequence_index=sequence_index,
        text_content=text_content,
        page_number=page_number,
        metadata_json={"layout": "text"},
    )


def test_build_for_section_returns_ordered_units_and_joined_context_text():
    """按 section 页码范围召回 DocumentUnit，并保留可追溯来源。"""
    section = _section()
    document_unit_repository = FakeDocumentUnitRepository(
        [
            _unit(
                unit_id="unit-3",
                sequence_index=3,
                text_content="第三页内容",
                page_number=3,
            ),
            _unit(
                unit_id="unit-1",
                sequence_index=1,
                text_content="第一页不属于本节",
                page_number=1,
            ),
            _unit(
                unit_id="unit-2",
                sequence_index=2,
                text_content="第二页内容",
                page_number=2,
            ),
        ]
    )
    builder = SectionContextBuilder(
        section_repository=FakeSectionRepository({section.id: section}),
        document_unit_repository=document_unit_repository,
    )

    context = builder.build_for_section(section.id)

    assert document_unit_repository.received_query == ("document-1", 2, 3)
    assert context.section_id == section.id
    assert context.document_id == "document-1"
    assert context.title == "第二章"
    assert context.start_page == 2
    assert context.end_page == 3
    assert [unit.document_unit_id for unit in context.units] == ["unit-2", "unit-3"]
    assert [unit.page_number for unit in context.units] == [2, 3]
    assert context.units[0].metadata_json == {"layout": "text"}
    assert context.context_text == "第二页内容\n\n第三页内容"


def test_build_for_section_returns_empty_context_when_no_units_in_page_range():
    section = _section(start_page=10, end_page=11)
    builder = SectionContextBuilder(
        section_repository=FakeSectionRepository({section.id: section}),
        document_unit_repository=FakeDocumentUnitRepository([]),
    )

    context = builder.build_for_section(section.id)

    assert context.units == []
    assert context.context_text == ""


@pytest.mark.parametrize(
    ("start_page", "end_page"),
    [
        (None, 3),
        (2, None),
        (4, 3),
    ],
)
def test_build_for_section_rejects_missing_or_invalid_page_range(
    start_page,
    end_page,
):
    section = _section(start_page=start_page, end_page=end_page)
    builder = SectionContextBuilder(
        section_repository=FakeSectionRepository({section.id: section}),
        document_unit_repository=FakeDocumentUnitRepository([]),
    )

    with pytest.raises(SectionPageRangeMissingError):
        builder.build_for_section(section.id)


def test_build_for_section_rejects_unknown_section_id():
    builder = SectionContextBuilder(
        section_repository=FakeSectionRepository({}),
        document_unit_repository=FakeDocumentUnitRepository([]),
    )

    with pytest.raises(SectionNotFoundError, match="missing-section"):
        builder.build_for_section("missing-section")


import pytest

from app.entities import DocumentUnit
from app.rag.page_index_builder import build_sections_from_units


def test_build_sections_prefers_heading_metadata() -> None:
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=3,
            text_content="Unit text",
            metadata_json={"headings": [{"title": "Chapter 1", "level": 1}]},
        )
    ]

    sections = build_sections_from_units("doc-1", units)

    assert len(sections) == 1
    assert sections[0].title == "Chapter 1"
    assert sections[0].level == 1
    assert sections[0].order_index == 0
    assert sections[0].start_page == 3
    assert sections[0].end_page == 3


def test_build_sections_falls_back_to_page_number_or_sequence() -> None:
    units = [
        DocumentUnit(document_id="doc-1", sequence_index=0, page_number=2, text_content="Page unit"),
        DocumentUnit(document_id="doc-1", sequence_index=1, text_content="No page unit"),
    ]

    sections = build_sections_from_units("doc-1", units)

    assert [section.title for section in sections] == ["Page 2", "Unit 2"]
    assert [section.level for section in sections] == [1, 1]


def test_build_sections_returns_empty_for_empty_units() -> None:
    assert build_sections_from_units("doc-1", []) == []

"""PageIndex 构建测试。"""

from app.entities import DocumentUnit
from app.rag.page_index_builder import PageIndexBuilder


def _unit(
    *,
    unit_id: str,
    document_id: str = "document-1",
    sequence_index: int,
    page_number: int,
    text_content: str,
) -> DocumentUnit:
    return DocumentUnit(
        id=unit_id,
        document_id=document_id,
        sequence_index=sequence_index,
        page_number=page_number,
        text_content=text_content,
        metadata_json={"language": "mixed"},
        parser_name="pdf-parser",
        parser_version="0.1",
    )


def test_build_from_document_units_orders_pages_and_preserves_source_metadata():
    """PageIndex 应以页码顺序输出页面，并保留原始 DocumentUnit 来源。"""
    units = [
        _unit(
            unit_id="unit-2",
            sequence_index=2,
            page_number=2,
            text_content="Deuxième page",
        ),
        _unit(
            unit_id="unit-1",
            sequence_index=1,
            page_number=1,
            text_content="第一页内容",
        ),
    ]

    page_index = PageIndexBuilder().build_from_document_units(
        document_id="document-1",
        document_units=units,
    )

    assert page_index.document_id == "document-1"
    assert page_index.page_count == 2
    assert [page.page_number for page in page_index.pages] == [1, 2]
    assert [page.document_unit_id for page in page_index.pages] == ["unit-1", "unit-2"]
    assert page_index.pages[0].text_content == "第一页内容"
    assert page_index.pages[0].char_count == len("第一页内容")
    assert page_index.pages[0].metadata_json == {"language": "mixed"}
    assert page_index.pages[0].parser_name == "pdf-parser"
    assert page_index.pages[0].parser_version == "0.1"


def test_build_from_document_units_ignores_units_without_page_number():
    units = [
        DocumentUnit(
            id="unit-without-page",
            document_id="document-1",
            sequence_index=1,
            page_number=None,
            text_content="没有页码的内容不能进入 PageIndex",
        ),
        _unit(
            unit_id="unit-1",
            sequence_index=2,
            page_number=1,
            text_content="第一页内容",
        ),
    ]

    page_index = PageIndexBuilder().build_from_document_units(
        document_id="document-1",
        document_units=units,
    )

    assert [page.document_unit_id for page in page_index.pages] == ["unit-1"]


def test_build_from_document_units_rejects_units_from_other_documents():
    units = [
        _unit(
            unit_id="foreign-unit",
            document_id="other-document",
            sequence_index=1,
            page_number=1,
            text_content="不属于当前文档",
        )
    ]

    page_index = PageIndexBuilder().build_from_document_units(
        document_id="document-1",
        document_units=units,
    )

    assert page_index.pages == []
    assert page_index.page_count == 0

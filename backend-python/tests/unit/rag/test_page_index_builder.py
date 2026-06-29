from app.entities import DocumentUnit
from app.rag.page_index_builder import build_sections_from_units


def test_build_sections_creates_tree_from_heading_levels() -> None:
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=1,
            text_content="第一章\n引言",
            metadata_json={
                "source_type": "pdf",
                "headings": [{"title": "第一章", "level": 1}],
            },
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=1,
            page_number=2,
            text_content="1.1 背景\n内容",
            metadata_json={
                "source_type": "pdf",
                "headings": [{"title": "1.1 背景", "level": 2}],
            },
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=2,
            page_number=3,
            text_content="继续背景内容",
            metadata_json={"source_type": "pdf", "headings": []},
        ),
    ]

    result = build_sections_from_units("doc-1", units)

    assert [section.title for section in result.sections] == ["第一章", "1.1 背景"]
    assert result.sections[0].parent_section_id is None
    assert result.sections[1].parent_section_id == result.sections[0].id
    assert result.sections[0].start_page == 1
    assert result.sections[0].end_page == 3
    assert result.sections[1].start_page == 2
    assert result.sections[1].end_page == 3
    assert result.section_unit_links[result.sections[0].id] == [units[0].id, units[1].id, units[2].id]
    assert result.section_unit_links[result.sections[1].id] == [units[1].id, units[2].id]


def test_build_sections_falls_back_to_page_nodes_for_plain_pdf() -> None:
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=5,
            text_content="Plain page",
            metadata_json={"source_type": "pdf", "headings": []},
        )
    ]

    result = build_sections_from_units("doc-1", units)

    assert [section.title for section in result.sections] == ["第 5 页"]
    assert result.sections[0].metadata_json["fallback_kind"] == "page"


def test_build_sections_uses_slide_title_for_ppt_nodes() -> None:
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=1,
            text_content="课程概览",
            metadata_json={
                "source_type": "ppt",
                "headings": [{"text": "课程概览", "level": 1}],
            },
        )
    ]

    result = build_sections_from_units("doc-1", units)

    assert result.sections[0].title == "课程概览"
    assert result.sections[0].metadata_json["source_type"] == "ppt"
    assert result.sections[0].metadata_json["node_kind"] == "slide"


def test_build_sections_returns_empty_for_empty_units() -> None:
    result = build_sections_from_units("doc-1", [])

    assert result.sections == []
    assert result.section_unit_links == {}


def test_build_sections_creates_tree_from_heading_candidates() -> None:
    """builder 应该从 metadata.headings 的候选构建真实章节树。"""
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=1,
            text_content="1. Introduction\nContent page 1",
            metadata_json={
                "source_type": "pdf",
                "headings": [
                    {"title": "1. Introduction", "level": 1, "confidence": 0.9, "source_block_id": "b-0", "numbering_pattern": "decimal"}
                ],
                "page_stats": {"primary_font_size": 10.5},
            },
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=1,
            page_number=2,
            text_content="1.1 Background\nContent page 2",
            metadata_json={
                "source_type": "pdf",
                "headings": [
                    {"title": "1.1 Background", "level": 2, "confidence": 0.85, "source_block_id": "b-0", "numbering_pattern": "decimal"}
                ],
                "page_stats": {"primary_font_size": 10.5},
            },
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=2,
            page_number=3,
            text_content="Content continues...",
            metadata_json={
                "source_type": "pdf",
                "headings": [],
                "page_stats": {"primary_font_size": 10.5},
            },
        ),
    ]

    result = build_sections_from_units("doc-1", units)

    assert len(result.sections) == 2
    assert result.sections[0].title == "1. Introduction"
    assert result.sections[0].level == 1
    assert result.sections[1].title == "1.1 Background"
    assert result.sections[1].level == 2
    assert result.sections[1].parent_section_id == result.sections[0].id
    assert result.sections[0].start_page == 1
    assert result.sections[0].end_page == 3
    assert result.sections[1].start_page == 2
    assert result.sections[1].end_page == 3


def test_build_sections_falls_back_to_per_page_for_plain_pdf() -> None:
    """无 heading 的 plain PDF 应该按页生成逐页 fallback sections，而不是单节点吞全文。"""
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=1,
            text_content="Page 1 content",
            metadata_json={"source_type": "pdf", "headings": []},
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=1,
            page_number=2,
            text_content="Page 2 content",
            metadata_json={"source_type": "pdf", "headings": []},
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=2,
            page_number=3,
            text_content="Page 3 content",
            metadata_json={"source_type": "pdf", "headings": []},
        ),
    ]

    result = build_sections_from_units("doc-1", units)

    assert len(result.sections) == 3
    assert result.sections[0].title == "第 1 页"
    assert result.sections[1].title == "第 2 页"
    assert result.sections[2].title == "第 3 页"
    assert result.sections[0].start_page == 1
    assert result.sections[1].start_page == 2
    assert result.sections[2].start_page == 3


def test_build_sections_filters_low_confidence_headings() -> None:
    """低置信度 heading 候选应该被过滤，不生成 section。"""
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=1,
            text_content="1. Introduction",
            metadata_json={
                "source_type": "pdf",
                "headings": [
                    {"title": "1. Introduction", "level": 1, "confidence": 0.3},  # 低于阈值 0.4
                ],
            },
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=1,
            page_number=2,
            text_content="Content page 2",
            metadata_json={"source_type": "pdf", "headings": []},
        ),
    ]

    result = build_sections_from_units("doc-1", units)

    # 低置信度候选被过滤，应该 fallback 到逐页节点
    assert len(result.sections) == 2
    assert result.sections[0].title == "第 1 页"
    assert result.sections[1].title == "第 2 页"


def test_build_sections_heading_at_confidence_threshold() -> None:
    """confidence 恰好等于阈值 0.4 的 heading 应该被接受。"""
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=1,
            text_content="1. Introduction",
            metadata_json={
                "source_type": "pdf",
                "headings": [
                    {"title": "1. Introduction", "level": 1, "confidence": 0.4},  # 恰好等于阈值
                ],
            },
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=1,
            page_number=2,
            text_content="Content page 2",
            metadata_json={"source_type": "pdf", "headings": []},
        ),
    ]

    result = build_sections_from_units("doc-1", units)

    # confidence=0.4 应该被接受，生成真实章节树
    assert len(result.sections) == 1
    assert result.sections[0].title == "1. Introduction"
    assert result.sections[0].level == 1


def test_build_sections_old_headings_without_confidence_use_default() -> None:
    """旧格式 headings（无 confidence 字段）应该使用默认值 0.5，通过阈值检查。"""
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=1,
            text_content="第一章",
            metadata_json={
                "source_type": "pdf",
                "headings": [{"title": "第一章", "level": 1}],  # 无 confidence 字段
            },
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=1,
            page_number=2,
            text_content="内容",
            metadata_json={"source_type": "pdf", "headings": []},
        ),
    ]

    result = build_sections_from_units("doc-1", units)

    # 旧格式 headings 使用默认 confidence=0.5，应该通过阈值检查
    assert len(result.sections) == 1
    assert result.sections[0].title == "第一章"

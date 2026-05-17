from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.entities import (
    AnalysisResult,
    ChatMessage,
    ChatSession,
    DocumentRecord,
    DocumentUnit,
    EmbeddingVector,
    Section,
    SectionUnitLink,
    Workspace,
)
from app.enums import (
    DEFAULT_WORKSPACE_TYPES,
    AnalysisType,
    DocumentFileType,
    DocumentStatus,
    MessageRole,
)


def assert_uuid(value: str) -> None:
    UUID(value)


def test_workspace_accepts_default_and_custom_types():
    assert DEFAULT_WORKSPACE_TYPES == ("course", "admin", "internship", "language", "other")

    workspace = Workspace(name="法国行政事务", type="caf")

    assert_uuid(workspace.id)
    assert workspace.type == "caf"
    assert isinstance(workspace.created_at, datetime)
    assert isinstance(workspace.updated_at, datetime)


def test_document_record_uses_file_type_and_status_enums():
    document = DocumentRecord(
        workspace_id="workspace_1",
        title="课程大纲",
        original_filename="syllabus.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/syllabus.pdf",
    )

    assert_uuid(document.id)
    assert document.status == DocumentStatus.UPLOADED
    assert document.page_count is None


def test_document_unit_supports_rag_metadata_and_parser_provenance():
    unit = DocumentUnit(
        document_id="document_1",
        sequence_index=3,
        text_content="作业需要在下周五前提交。",
        page_number=2,
        start_char=120,
        end_char=158,
        token_count=8,
        metadata_json={
            "source_file": "syllabus.pdf",
            "section_title": "作业要求",
            "language": "zh",
            "chunk_index": 3,
        },
        raw_content_json={
            "bbox": [10, 20, 300, 80],
            "ocr_confidence": 0.98,
        },
        parser_name="recursive_text_splitter",
        parser_version="1.0",
        external_id="external_node_123",
    )

    assert_uuid(unit.id)
    assert unit.metadata_json["chunk_index"] == 3
    assert unit.raw_content_json["bbox"] == [10, 20, 300, 80]
    assert unit.external_id == "external_node_123"
    assert isinstance(unit.created_at, datetime)


def test_document_unit_field_descriptions_are_available():
    assert DocumentUnit.model_fields["sequence_index"].description == (
        "同一文档内的内容单元顺序；持久化层应保证同一文档内唯一。"
    )
    assert DocumentUnit.model_fields["text_content"].description == "统一正文内容，用于展示、检索和 AI 分析。"
    assert DocumentUnit.model_fields["metadata_json"].description == "用于检索、过滤和展示的元数据。"
    assert DocumentUnit.model_fields["raw_content_json"].description == "解析器输出的原始布局或 OCR 信息。"


def test_section_supports_header_hierarchy_and_parser_metadata():
    parent = Section(
        document_id="document_1",
        title="课程概览",
        level=1,
        order_index=0,
        parser_name="markdown_header_splitter",
        external_id="header_1",
    )
    child = Section(
        document_id="document_1",
        parent_section_id=parent.id,
        title="作业要求",
        level=2,
        order_index=1,
        metadata_json={"header_path": ["课程概览", "作业要求"]},
    )

    assert_uuid(parent.id)
    assert child.parent_section_id == parent.id
    assert child.metadata_json["header_path"] == ["课程概览", "作业要求"]


def test_section_unit_link_models_many_to_many_relationship():
    link_a = SectionUnitLink(section_id="section_1", document_unit_id="unit_1", order_index=0)
    link_b = SectionUnitLink(section_id="section_1", document_unit_id="unit_2", order_index=1)
    link_c = SectionUnitLink(section_id="section_2", document_unit_id="unit_2", order_index=0)

    section_1_units = [link.document_unit_id for link in [link_a, link_b] if link.section_id == "section_1"]
    unit_2_sections = [link.section_id for link in [link_b, link_c] if link.document_unit_id == "unit_2"]

    assert section_1_units == ["unit_1", "unit_2"]
    assert unit_2_sections == ["section_1", "section_2"]


def test_section_unit_link_documents_persistence_uniqueness_rules():
    assert SectionUnitLink.model_fields["document_unit_id"].description == (
        "关联的内容单元 ID；持久化层应保证同一小节内不重复关联。"
    )
    assert SectionUnitLink.model_fields["order_index"].description == (
        "内容单元在该小节中的顺序；持久化层应保证同一小节内唯一。"
    )


def test_embedding_vector_keeps_logical_float_vector():
    vector = EmbeddingVector(
        document_unit_id="unit_1",
        embedding_model="local-embedding-model",
        vector_dimension=3,
        vector=[0.1, 0.2, 0.3],
    )

    assert vector.vector == [0.1, 0.2, 0.3]


def test_embedding_vector_rejects_vector_dimension_mismatch():
    with pytest.raises(ValidationError, match="向量长度必须等于 vector_dimension"):
        EmbeddingVector(
            document_unit_id="unit_1",
            embedding_model="local-embedding-model",
            vector_dimension=3,
            vector=[0.1, 0.2],
        )


def test_embedding_vector_requires_positive_dimension():
    with pytest.raises(ValidationError):
        EmbeddingVector(
            document_unit_id="unit_1",
            embedding_model="local-embedding-model",
            vector_dimension=0,
        )


def test_analysis_result_supports_full_document_and_section_analysis():
    full_document = AnalysisResult(
        document_id="document_1",
        analysis_type=AnalysisType.FULL_DOCUMENT,
        language="zh",
        content_markdown="全文摘要",
    )
    section = AnalysisResult(
        document_id="document_1",
        section_id="section_1",
        analysis_type=AnalysisType.SECTION,
        language="zh",
        content_markdown="小节摘要",
        content_json={"key_points": ["截止日期"]},
        model_name="local-model",
        prompt_version="analysis-v1",
    )

    assert full_document.section_id is None
    assert section.section_id == "section_1"
    assert section.content_json["key_points"] == ["截止日期"]


def test_analysis_result_requires_section_id_for_section_analysis():
    with pytest.raises(ValidationError, match="小节解析必须提供 section_id"):
        AnalysisResult(
            document_id="document_1",
            analysis_type=AnalysisType.SECTION,
            language="zh",
            content_markdown="小节摘要",
        )


def test_analysis_result_rejects_section_id_for_full_document_analysis():
    with pytest.raises(ValidationError, match="全文解析不能设置 section_id"):
        AnalysisResult(
            document_id="document_1",
            section_id="section_1",
            analysis_type=AnalysisType.FULL_DOCUMENT,
            language="zh",
            content_markdown="全文摘要",
        )


def test_chat_session_scopes_to_workspace_or_document_only():
    workspace_session = ChatSession(workspace_id="workspace_1", title="通用问答")
    document_session = ChatSession(
        workspace_id="workspace_1",
        document_id="document_1",
        title="文档问答",
    )

    assert workspace_session.document_id is None
    assert document_session.document_id == "document_1"


def test_chat_message_role_is_user_or_agent():
    user_message = ChatMessage(
        session_id="session_1",
        role=MessageRole.USER,
        content="作业是什么？",
    )
    agent_message = ChatMessage(
        session_id="session_1",
        role=MessageRole.AGENT,
        content="作业需要在周五前提交。",
        source_context_json={"document_unit_ids": ["unit_1"]},
    )

    assert user_message.role == MessageRole.USER
    assert agent_message.role == MessageRole.AGENT
    assert agent_message.source_context_json["document_unit_ids"] == ["unit_1"]

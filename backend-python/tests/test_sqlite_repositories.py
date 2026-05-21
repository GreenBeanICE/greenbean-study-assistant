import sqlite3

import pytest

from app.db.init_db import initialize_database
from app.entities import (
    AnalysisResult,
    ChatMessage,
    ChatSession,
    Chunk,
    DocumentRecord,
    DocumentUnit,
    Section,
)
from app.enums import AnalysisType, DocumentFileType, MessageRole
from app.repositories.analysis_result_repository import AnalysisResultRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.repositories.embedding_repository import (
    EmbeddingDimensionError,
    EmbeddingRepository,
    MissingChunkError,
)
from app.repositories.section_repository import SectionRepository


def load_test_sqlite_vec(connection: sqlite3.Connection) -> None:
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


@pytest.fixture
def initialized_database_path(tmp_path):
    result = initialize_database(
        data_dir=tmp_path / "data",
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )
    return result.database_path


def make_core_learning_data():
    document = DocumentRecord(
        workspace_id="workspace_1",
        title="Course Deck",
        original_filename="course.pptx",
        file_type=DocumentFileType.PPTX,
        file_path="data/uploads/course.pptx",
        page_count=12,
    )
    unit = DocumentUnit(
        document_id=document.id,
        sequence_index=0,
        text_content="Slide 1 introduces the course objectives.",
        page_number=1,
        metadata_json={"unit_kind": "slide"},
    )
    section = Section(
        document_id=document.id,
        title="Course objectives",
        level=1,
        order_index=0,
        start_page=1,
        end_page=2,
        metadata_json={"source_unit_ids": [unit.id]},
    )
    chunk = Chunk(
        document_unit_id=unit.id,
        sequence_index=0,
        text_content="Course objectives and grading policy.",
        start_char=0,
        end_char=37,
        token_count=6,
    )
    analysis_result = AnalysisResult(
        document_id=document.id,
        section_id=section.id,
        analysis_type=AnalysisType.SECTION,
        language="zh",
        content_markdown="课程目标总结",
        model_name="test-model",
    )
    chat_session = ChatSession(
        workspace_id="workspace_1",
        document_id=document.id,
        title="Course Q&A",
    )
    chat_message = ChatMessage(
        session_id=chat_session.id,
        role=MessageRole.USER,
        content="课程考核方式是什么？",
        source_context_json={"chunk_ids": [chunk.id]},
    )
    return document, unit, section, chunk, analysis_result, chat_session, chat_message


def test_repositories_persist_core_learning_data_after_reconnect(initialized_database_path):
    document, unit, section, chunk, analysis_result, chat_session, chat_message = make_core_learning_data()

    with sqlite3.connect(initialized_database_path) as connection:
        DocumentRepository(connection).save(document)
        DocumentUnitRepository(connection).save(unit)
        SectionRepository(connection).save(section)
        ChunkRepository(connection).save(chunk)
        AnalysisResultRepository(connection).save(analysis_result)
        ChatSessionRepository(connection).save(chat_session)
        ChatMessageRepository(connection).save(chat_message)

    with sqlite3.connect(initialized_database_path) as connection:
        assert DocumentRepository(connection).get_by_id(document.id).title == "Course Deck"
        assert DocumentUnitRepository(connection).get_by_id(unit.id).text_content == unit.text_content
        assert SectionRepository(connection).get_by_id(section.id).title == "Course objectives"
        assert ChunkRepository(connection).get_by_id(chunk.id).document_unit_id == unit.id
        assert AnalysisResultRepository(connection).get_by_id(analysis_result.id).section_id == section.id
        assert ChatSessionRepository(connection).get_by_id(chat_session.id).document_id == document.id
        assert ChatMessageRepository(connection).get_by_id(chat_message.id).session_id == chat_session.id


def test_embedding_repository_saves_chunk_embedding_and_traces_to_document_unit(initialized_database_path):
    document, unit, _, chunk, *_ = make_core_learning_data()

    with sqlite3.connect(initialized_database_path) as connection:
        DocumentRepository(connection).save(document)
        DocumentUnitRepository(connection).save(unit)
        ChunkRepository(connection).save(chunk)

        embedding = EmbeddingRepository(connection, embedding_dimension=8).save_for_chunk(
            chunk_id=chunk.id,
            embedding_model="test-embedding-model",
            vector=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
        )

    with sqlite3.connect(initialized_database_path) as connection:
        persisted = EmbeddingRepository(connection, embedding_dimension=8).get_by_chunk_id(chunk.id)
        persisted_chunk = ChunkRepository(connection).get_by_id(persisted.chunk_id)

    assert embedding.chunk_id == chunk.id
    assert persisted.chunk_id == chunk.id
    assert persisted.vector_dimension == 8
    assert persisted.vector == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    assert persisted_chunk.document_unit_id == unit.id


def test_embedding_repository_rejects_dimension_mismatch(initialized_database_path):
    document, unit, _, chunk, *_ = make_core_learning_data()

    with sqlite3.connect(initialized_database_path) as connection:
        DocumentRepository(connection).save(document)
        DocumentUnitRepository(connection).save(unit)
        ChunkRepository(connection).save(chunk)

        with pytest.raises(EmbeddingDimensionError, match="dimension"):
            EmbeddingRepository(connection, embedding_dimension=8).save_for_chunk(
                chunk_id=chunk.id,
                embedding_model="test-embedding-model",
                vector=[0.1, 0.2],
            )


def test_embedding_repository_rejects_missing_chunk(initialized_database_path):
    with sqlite3.connect(initialized_database_path) as connection:
        with pytest.raises(MissingChunkError, match="missing-chunk"):
            EmbeddingRepository(connection, embedding_dimension=8).save_for_chunk(
                chunk_id="missing-chunk",
                embedding_model="test-embedding-model",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
            )


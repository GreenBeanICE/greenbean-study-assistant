"""sqlite-vec Chunk 向量索引持久化测试。"""

import pytest

sqlite_vec = pytest.importorskip("sqlite_vec")

from app.db.init_db import initialize_database, load_sqlite_vec_extension
from app.db.orm import create_database_engine, create_session_factory
from app.entities import Chunk, DocumentRecord, DocumentUnit
from app.enums import DocumentFileType
from app.rag.retriever import SQLiteVecRetriever
from app.rag.vector_index_builder import SQLiteVecIndexBuilder
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository


@pytest.fixture
def session_factory(tmp_path):
    result = initialize_database(
        data_dir=tmp_path / "data",
        sqlite_vec_loader=load_sqlite_vec_extension,
        embedding_dimension=2,
    )
    engine = create_database_engine(
        result.database_path,
        sqlite_vec_loader=load_sqlite_vec_extension,
    )
    yield create_session_factory(engine)
    engine.dispose()


def _document() -> DocumentRecord:
    return DocumentRecord(
        workspace_id="workspace-1",
        title="Embedding Test",
        original_filename="embedding.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/embedding.pdf",
        page_count=1,
    )


def _save_source(session) -> tuple[Chunk, Chunk]:
    document = _document()
    unit = DocumentUnit(
        document_id=document.id,
        sequence_index=0,
        page_number=1,
        text_content="苹果 香蕉 法语",
    )
    chunk_a = Chunk(
        document_unit_id=unit.id,
        sequence_index=0,
        text_content="苹果 香蕉",
        start_char=0,
        end_char=5,
        metadata_json={"page_number": 1},
    )
    chunk_b = Chunk(
        document_unit_id=unit.id,
        sequence_index=1,
        text_content="法国 高等教育",
        start_char=6,
        end_char=12,
        metadata_json={"page_number": 1},
    )

    DocumentRepository(session).save(document)
    DocumentUnitRepository(session).save(unit)
    ChunkRepository(session).save(chunk_a)
    ChunkRepository(session).save(chunk_b)
    return chunk_a, chunk_b


def test_sqlite_vec_index_stores_vectors_and_retrieves_nearest_chunk(session_factory):
    with session_factory() as session:
        chunk_a, chunk_b = _save_source(session)
        index_builder = SQLiteVecIndexBuilder(session=session, embedding_dimension=2)

        index_builder.upsert_chunk_embedding(
            chunk_id=chunk_a.id,
            vector=[1.0, 0.0],
            embedding_model="test-embedding",
        )
        index_builder.upsert_chunk_embedding(
            chunk_id=chunk_b.id,
            vector=[0.0, 1.0],
            embedding_model="test-embedding",
        )
        session.commit()

    with session_factory() as session:
        retriever = SQLiteVecRetriever(session=session, embedding_dimension=2)

        results = retriever.search(query_vector=[0.95, 0.05], top_k=1)

    assert len(results) == 1
    assert results[0].chunk_id == chunk_a.id
    assert results[0].document_unit_id == chunk_a.document_unit_id
    assert results[0].text_content == "苹果 香蕉"
    assert results[0].page_number == 1
    assert results[0].distance >= 0

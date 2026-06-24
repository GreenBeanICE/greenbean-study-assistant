import pytest

from app.db.connection import create_app_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.entities import Chunk, DocumentRecord, DocumentUnit
from app.enums import DocumentFileType
from app.providers.base import EmbeddingResult
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.services.embedding_service import EmbeddingService


def _fake_sqlite_vec_loader(connection):
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


class FakeProvider:
    def __init__(self, result: EmbeddingResult) -> None:
        self.result = result

    async def create_embedding(self, input, model=None):
        return self.result


@pytest.fixture
def session_factory(tmp_path):
    database_path = tmp_path / "data" / "embedding.sqlite3"
    return create_app_session_factory(
        database_path=database_path,
        embedding_dimension=2,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )


def _seed_chunks(session_factory):
    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit = DocumentUnit(document_id=document.id, sequence_index=0, text_content="Source")
    chunks = [
        Chunk(document_unit_id=unit.id, sequence_index=0, text_content="chunk-a"),
        Chunk(document_unit_id=unit.id, sequence_index=1, text_content="chunk-b"),
    ]

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(unit)
        for chunk in chunks:
            ChunkRepository(uow.session).save(chunk)
        uow.commit()
    return chunks


@pytest.mark.asyncio
async def test_embed_chunks_saves_all_vectors(session_factory) -> None:
    chunks = _seed_chunks(session_factory)
    service = EmbeddingService(
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        provider=FakeProvider(
            EmbeddingResult(embeddings=[[0.1, 0.2], [0.3, 0.4]], model="embed-small")
        ),
        embedding_dimension=2,
    )

    saved = await service.embed_chunks(chunks, model="embed-small")

    assert len(saved) == 2


@pytest.mark.asyncio
async def test_embed_chunks_rolls_back_when_embedding_count_mismatches(session_factory) -> None:
    chunks = _seed_chunks(session_factory)
    service = EmbeddingService(
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        provider=FakeProvider(EmbeddingResult(embeddings=[[0.1, 0.2]], model="embed-small")),
        embedding_dimension=2,
    )

    with pytest.raises(ValueError, match="Embedding count mismatch"):
        await service.embed_chunks(chunks, model="embed-small")

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert EmbeddingRepository(uow.session, embedding_dimension=2).get_by_chunk_id(chunks[0].id) is None

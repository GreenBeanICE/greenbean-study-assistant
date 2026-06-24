from unittest.mock import patch

import pytest

from app.db.connection import create_app_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.entities import Chunk, DocumentRecord, DocumentUnit
from app.enums import DocumentFileType
from app.enums.purpose import Purpose
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
        self.last_model = None

    async def create_embedding(self, input, model=None):
        self.last_model = model
        return self.result


@pytest.fixture
def session_factory(tmp_path):
    return create_app_session_factory(
        database_path=tmp_path / "data" / "embedding.sqlite3",
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


def _embedding_config_factory(dimension: int):
    from app.enums.api_mode import ApiMode
    from app.entities.provider_config import ProviderConfig

    return ProviderConfig(
        name="embed-cfg",
        api_mode=ApiMode.OPENAI_COMPAT,
        api_key="sk-embed",
        api_host="https://api.embed.com",
        model_id="embed-model",
        display_name="Embed",
        purpose=Purpose.EMBEDDING,
        embedding_dimension=dimension,
    )


@pytest.mark.asyncio
async def test_embed_chunks_uses_active_embedding_config(session_factory):
    chunks = _seed_chunks(session_factory)
    fake_provider = FakeProvider(
        EmbeddingResult(embeddings=[[0.1, 0.2], [0.3, 0.4]], model="embed-model")
    )
    service = EmbeddingService(uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory))
    with patch(
        "app.services.embedding_service.ProviderRegistry.get_active_embedding",
        return_value=fake_provider,
    ), patch(
        "app.services.embedding_service.ProviderRegistry.get_active_config",
        return_value=_embedding_config_factory(2),
    ):
        saved = await service.embed_chunks(chunks)

    assert len(saved) == 2


@pytest.mark.asyncio
async def test_embed_chunks_passes_config_model_id(session_factory):
    chunks = _seed_chunks(session_factory)
    fake_provider = FakeProvider(
        EmbeddingResult(embeddings=[[0.1, 0.2], [0.3, 0.4]], model="embed-model")
    )
    service = EmbeddingService(uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory))
    with patch(
        "app.services.embedding_service.ProviderRegistry.get_active_embedding",
        return_value=fake_provider,
    ), patch(
        "app.services.embedding_service.ProviderRegistry.get_active_config",
        return_value=_embedding_config_factory(2),
    ):
        await service.embed_chunks(chunks)

    assert fake_provider.last_model == "embed-model"


@pytest.mark.asyncio
async def test_embed_chunks_rolls_back_when_count_mismatches(session_factory):
    chunks = _seed_chunks(session_factory)
    fake_provider = FakeProvider(
        EmbeddingResult(embeddings=[[0.1, 0.2]], model="embed-model")
    )
    service = EmbeddingService(uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory))
    with patch(
        "app.services.embedding_service.ProviderRegistry.get_active_embedding",
        return_value=fake_provider,
    ), patch(
        "app.services.embedding_service.ProviderRegistry.get_active_config",
        return_value=_embedding_config_factory(2),
    ):
        with pytest.raises(ValueError, match="Embedding count mismatch"):
            await service.embed_chunks(chunks)

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert (
            EmbeddingRepository(uow.session, embedding_dimension=2).get_by_chunk_id(chunks[0].id)
            is None
        )

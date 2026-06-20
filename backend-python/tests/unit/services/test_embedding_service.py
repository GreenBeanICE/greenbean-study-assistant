from unittest.mock import AsyncMock, MagicMock, call

import pytest

from app.entities import Chunk
from app.providers.embedding_base import (
    EmbeddingModelInfo,
    EmbeddingProviderError,
)
from app.providers.embedding_registry import (
    EmbeddingProviderNotFoundError,
    EmbeddingProviderRegistry,
)
from app.services.embedding_service import (
    EmbeddingCountMismatchError,
    EmbeddingService,
)

MODEL_INFO = EmbeddingModelInfo(
    provider="google",
    model_id="gemini-embedding-001",
    dimension=3,
)


def make_chunk(index: int, text: str) -> Chunk:
    return Chunk(
        id=f"chunk-{index}",
        document_unit_id="unit-1",
        sequence_index=index,
        text_content=text,
    )


@pytest.fixture(autouse=True)
def clear_registry():
    EmbeddingProviderRegistry.clear()
    yield
    EmbeddingProviderRegistry.clear()


@pytest.fixture
def provider():
    mock = MagicMock()
    mock.embed_documents = AsyncMock()
    mock.embed_query = AsyncMock()
    mock.get_model_info.return_value = MODEL_INFO
    return mock


@pytest.fixture
def repository():
    return MagicMock()


@pytest.mark.asyncio
async def test_embed_chunks_preserves_order_and_persists_each_vector(
    provider, repository
):
    chunks = [make_chunk(0, "中文"), make_chunk(1, "français")]
    vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    provider.embed_documents.return_value = vectors
    repository.save_for_chunk.side_effect = ["saved-1", "saved-2"]
    service = EmbeddingService(repository, provider=provider)

    result = await service.embed_chunks(chunks)

    provider.embed_documents.assert_awaited_once_with(["中文", "français"])
    assert repository.save_for_chunk.call_args_list == [
        call(
            chunk_id="chunk-0",
            embedding_model="gemini-embedding-001",
            vector=vectors[0],
        ),
        call(
            chunk_id="chunk-1",
            embedding_model="gemini-embedding-001",
            vector=vectors[1],
        ),
    ]
    assert result == ["saved-1", "saved-2"]


@pytest.mark.asyncio
async def test_embed_chunks_returns_empty_without_calling_dependencies(
    provider, repository
):
    service = EmbeddingService(repository, provider=provider)

    assert await service.embed_chunks([]) == []
    provider.embed_documents.assert_not_awaited()
    repository.save_for_chunk.assert_not_called()


@pytest.mark.asyncio
async def test_embed_chunks_rejects_vector_count_mismatch_before_persistence(
    provider, repository
):
    provider.embed_documents.return_value = [[0.1, 0.2, 0.3]]
    service = EmbeddingService(repository, provider=provider)

    with pytest.raises(EmbeddingCountMismatchError, match="embedding count"):
        await service.embed_chunks(
            [make_chunk(0, "first"), make_chunk(1, "second")]
        )

    repository.save_for_chunk.assert_not_called()


@pytest.mark.asyncio
async def test_embed_chunks_does_not_persist_when_provider_fails(
    provider, repository
):
    provider.embed_documents.side_effect = EmbeddingProviderError("request failed")
    service = EmbeddingService(repository, provider=provider)

    with pytest.raises(EmbeddingProviderError, match="request failed"):
        await service.embed_chunks([make_chunk(0, "text")])

    repository.save_for_chunk.assert_not_called()


@pytest.mark.asyncio
async def test_embed_query_returns_vector_without_persistence(provider, repository):
    provider.embed_query.return_value = [0.1, 0.2, 0.3]
    service = EmbeddingService(repository, provider=provider)

    assert await service.embed_query("database normalization") == [0.1, 0.2, 0.3]
    provider.embed_query.assert_awaited_once_with("database normalization")
    repository.save_for_chunk.assert_not_called()


@pytest.mark.asyncio
async def test_service_uses_active_registry_provider(provider, repository):
    provider.embed_documents.return_value = [[0.1, 0.2, 0.3]]
    repository.save_for_chunk.return_value = "saved"
    EmbeddingProviderRegistry.activate(provider)
    service = EmbeddingService(repository)

    assert await service.embed_chunks([make_chunk(0, "text")]) == ["saved"]
    provider.embed_documents.assert_awaited_once_with(["text"])


@pytest.mark.asyncio
async def test_service_requires_provider_when_embedding(repository):
    service = EmbeddingService(repository)

    with pytest.raises(EmbeddingProviderNotFoundError):
        await service.embed_query("query")

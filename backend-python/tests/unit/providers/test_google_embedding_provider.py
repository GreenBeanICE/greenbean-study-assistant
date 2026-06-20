from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.config.embedding_settings import GoogleEmbeddingSettings
from app.providers.embedding_base import (
    EmbeddingProviderError,
    EmbeddingValidationError,
)
from app.providers.google_embedding_provider import GoogleEmbeddingProvider


VECTOR_DIMENSION = 768
SECRET_API_KEY = "secret-google-api-key"


def make_embedding(value: float, dimension: int = VECTOR_DIMENSION):
    return SimpleNamespace(values=[value] * dimension)


def make_response(*embeddings):
    return SimpleNamespace(embeddings=list(embeddings))


@pytest.fixture
def settings() -> GoogleEmbeddingSettings:
    return GoogleEmbeddingSettings(api_key=SECRET_API_KEY)


@pytest.fixture
def google_client():
    client = MagicMock()
    client.aio.models.embed_content = AsyncMock()
    return client


@pytest.fixture
def provider(settings, google_client) -> GoogleEmbeddingProvider:
    return GoogleEmbeddingProvider(settings=settings, client=google_client)


def test_settings_use_safe_defaults_and_hide_api_key(settings):
    assert settings.model_id == "gemini-embedding-001"
    assert settings.output_dimension == VECTOR_DIMENSION
    assert settings.batch_size == 16
    assert SECRET_API_KEY not in repr(settings)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [("output_dimension", 0), ("batch_size", 0)],
)
def test_settings_reject_non_positive_values(field_name, invalid_value):
    with pytest.raises(ValidationError):
        GoogleEmbeddingSettings(
            api_key=SECRET_API_KEY,
            **{field_name: invalid_value},
        )


def test_provider_reports_model_information(provider):
    model_info = provider.get_model_info()

    assert model_info.provider == "google"
    assert model_info.model_id == "gemini-embedding-001"
    assert model_info.dimension == VECTOR_DIMENSION


@pytest.mark.asyncio
async def test_embed_documents_uses_document_task_and_preserves_language_text(
    provider,
    google_client,
):
    documents = ["中文课程内容", "Contenu du cours en français"]
    google_client.aio.models.embed_content.return_value = make_response(
        make_embedding(0.1),
        make_embedding(0.2),
    )

    vectors = await provider.embed_documents(documents)

    assert vectors == [[0.1] * VECTOR_DIMENSION, [0.2] * VECTOR_DIMENSION]
    kwargs = google_client.aio.models.embed_content.await_args.kwargs
    assert kwargs["model"] == "gemini-embedding-001"
    assert kwargs["contents"] == documents
    assert kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"
    assert kwargs["config"].output_dimensionality == VECTOR_DIMENSION


@pytest.mark.asyncio
async def test_embed_query_uses_query_task(provider, google_client):
    google_client.aio.models.embed_content.return_value = make_response(
        make_embedding(0.3)
    )

    vector = await provider.embed_query("Quelle est la définition ?")

    assert vector == [0.3] * VECTOR_DIMENSION
    kwargs = google_client.aio.models.embed_content.await_args.kwargs
    assert kwargs["contents"] == ["Quelle est la définition ?"]
    assert kwargs["config"].task_type == "RETRIEVAL_QUERY"


@pytest.mark.asyncio
async def test_embed_documents_splits_batches_and_preserves_order(google_client):
    settings = GoogleEmbeddingSettings(api_key=SECRET_API_KEY, batch_size=2)
    provider = GoogleEmbeddingProvider(settings=settings, client=google_client)
    google_client.aio.models.embed_content.side_effect = [
        make_response(make_embedding(0.1), make_embedding(0.2)),
        make_response(make_embedding(0.3), make_embedding(0.4)),
        make_response(make_embedding(0.5)),
    ]

    vectors = await provider.embed_documents(["a", "b", "c", "d", "e"])

    assert [vector[0] for vector in vectors] == [0.1, 0.2, 0.3, 0.4, 0.5]
    assert google_client.aio.models.embed_content.await_count == 3
    batches = [
        call.kwargs["contents"]
        for call in google_client.aio.models.embed_content.await_args_list
    ]
    assert batches == [["a", "b"], ["c", "d"], ["e"]]


@pytest.mark.asyncio
async def test_embed_documents_returns_empty_without_api_call(provider, google_client):
    assert await provider.embed_documents([]) == []
    google_client.aio.models.embed_content.assert_not_awaited()


@pytest.mark.asyncio
async def test_embed_query_rejects_blank_text(provider, google_client):
    with pytest.raises(EmbeddingValidationError, match="query must not be blank"):
        await provider.embed_query("   ")

    google_client.aio.models.embed_content.assert_not_awaited()


@pytest.mark.asyncio
async def test_provider_rejects_response_count_mismatch(provider, google_client):
    google_client.aio.models.embed_content.return_value = make_response(
        make_embedding(0.1)
    )

    with pytest.raises(EmbeddingValidationError, match="embedding count"):
        await provider.embed_documents(["first", "second"])


@pytest.mark.asyncio
async def test_provider_rejects_response_dimension_mismatch(provider, google_client):
    google_client.aio.models.embed_content.return_value = make_response(
        make_embedding(0.1, dimension=2)
    )

    with pytest.raises(EmbeddingValidationError, match="embedding dimension"):
        await provider.embed_query("valid query")


@pytest.mark.asyncio
async def test_provider_wraps_google_error_without_leaking_api_key(
    provider,
    google_client,
):
    google_client.aio.models.embed_content.side_effect = RuntimeError(
        f"request failed with {SECRET_API_KEY}"
    )

    with pytest.raises(EmbeddingProviderError) as exc_info:
        await provider.embed_query("valid query")

    assert SECRET_API_KEY not in str(exc_info.value)


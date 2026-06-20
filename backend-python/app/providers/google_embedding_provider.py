"""Google Gemini Embedding Provider。"""

from typing import Any

from google import genai
from google.genai import types

from app.config.embedding_settings import GoogleEmbeddingSettings
from app.providers.embedding_base import (
    EmbeddingModelInfo,
    EmbeddingProvider,
    EmbeddingProviderError,
    EmbeddingValidationError,
)

GOOGLE_PROVIDER_NAME = "google"
RETRIEVAL_DOCUMENT_TASK = "RETRIEVAL_DOCUMENT"
RETRIEVAL_QUERY_TASK = "RETRIEVAL_QUERY"


class GoogleEmbeddingProvider(EmbeddingProvider):
    """通过 Google Gen AI SDK 生成 Embedding。"""

    def __init__(
        self,
        settings: GoogleEmbeddingSettings,
        client: Any | None = None,
    ) -> None:
        self._settings = settings
        self._client = client or genai.Client(
            api_key=settings.api_key.get_secret_value()
        )

    def get_model_info(self) -> EmbeddingModelInfo:
        return EmbeddingModelInfo(
            provider=GOOGLE_PROVIDER_NAME,
            model_id=self._settings.model_id,
            dimension=self._settings.output_dimension,
        )

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._settings.batch_size):
            batch = texts[start : start + self._settings.batch_size]
            vectors.extend(await self._embed(batch, RETRIEVAL_DOCUMENT_TASK))
        return vectors

    async def embed_query(self, query: str) -> list[float]:
        if not query.strip():
            raise EmbeddingValidationError("query must not be blank")
        return (await self._embed([query], RETRIEVAL_QUERY_TASK))[0]

    async def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        try:
            response = await self._client.aio.models.embed_content(
                model=self._settings.model_id,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self._settings.output_dimension,
                ),
            )
            return self._validated_vectors(response, len(texts))
        except EmbeddingValidationError:
            raise
        except Exception as exc:
            raise EmbeddingProviderError("Google Embedding request failed") from exc

    def _validated_vectors(
        self, response: Any, expected_count: int
    ) -> list[list[float]]:
        embeddings = response.embeddings
        if embeddings is None or len(embeddings) != expected_count:
            actual_count = 0 if embeddings is None else len(embeddings)
            raise EmbeddingValidationError(
                f"embedding count mismatch: expected {expected_count}, got {actual_count}"
            )

        vectors: list[list[float]] = []
        for embedding in embeddings:
            values = embedding.values
            if values is None or len(values) != self._settings.output_dimension:
                actual_dimension = 0 if values is None else len(values)
                raise EmbeddingValidationError(
                    "embedding dimension mismatch: "
                    f"expected {self._settings.output_dimension}, got {actual_dimension}"
                )
            vectors.append(list(values))
        return vectors

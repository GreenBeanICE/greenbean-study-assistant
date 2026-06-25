# Embedding 服务占位文件，后续用于向量生成和嵌入管理。

from app.entities import Chunk
from app.providers.embedding_base import (
    EmbeddingProvider,
    EmbeddingValidationError,
)
from app.providers.embedding_registry import EmbeddingProviderRegistry
from app.repositories.embedding_repository import ChunkEmbedding, EmbeddingRepository


class EmbeddingCountMismatchError(EmbeddingValidationError):
    """Provider 返回的向量数量与输入 Chunk 数量不一致。"""


class EmbeddingService:
    """协调 Embedding Provider 与持久化 Repository。"""

    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
        *,
        provider: EmbeddingProvider | None = None,
    ) -> None:
        self._embedding_repository = embedding_repository
        self._provider = provider

    async def embed_chunks(self, chunks: list[Chunk]) -> list[ChunkEmbedding]:
        if not chunks:
            return []

        provider = self._get_provider()
        vectors = await provider.embed_documents(
            [chunk.text_content for chunk in chunks]
        )
        if len(vectors) != len(chunks):
            raise EmbeddingCountMismatchError(
                "embedding count mismatch: "
                f"expected {len(chunks)}, got {len(vectors)}"
            )

        model_id = provider.get_model_info().model_id
        return [
            self._embedding_repository.save_for_chunk(
                chunk_id=chunk.id,
                embedding_model=model_id,
                vector=vector,
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]

    async def embed_query(self, query: str) -> list[float]:
        return await self._get_provider().embed_query(query)

    def _get_provider(self) -> EmbeddingProvider:
        return self._provider or EmbeddingProviderRegistry.get_active()

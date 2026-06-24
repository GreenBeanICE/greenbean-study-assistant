from app.repositories.embedding_repository import EmbeddingRepository


class EmbeddingService:
    def __init__(self, uow_factory, provider, *, embedding_dimension: int) -> None:
        self.uow_factory = uow_factory
        self.provider = provider
        self.embedding_dimension = embedding_dimension

    async def embed_chunks(self, chunks, *, model: str):
        if model is None:
            raise ValueError("Embedding model is required")

        texts = [chunk.text_content for chunk in chunks]
        result = await self.provider.create_embedding(texts, model=model)
        if len(result.embeddings) != len(chunks):
            raise ValueError(
                f"Embedding count mismatch: expected {len(chunks)}, got {len(result.embeddings)}"
            )

        with self.uow_factory() as uow:
            repo = EmbeddingRepository(uow.session, embedding_dimension=self.embedding_dimension)
            saved = []
            for chunk, vector in zip(chunks, result.embeddings, strict=True):
                saved.append(
                    repo.save_for_chunk(
                        chunk_id=chunk.id,
                        embedding_model=result.model,
                        vector=vector,
                    )
                )
            uow.commit()
            return saved

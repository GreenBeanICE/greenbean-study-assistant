from app.enums.purpose import Purpose
from app.providers.registry import ProviderRegistry
from app.repositories.embedding_repository import EmbeddingRepository


class EmbeddingService:
    def __init__(self, uow_factory) -> None:
        self.uow_factory = uow_factory

    async def embed_chunks(self, chunks, *, model: str | None = None):
        provider = ProviderRegistry.get_active_embedding()
        config = ProviderRegistry.get_active_config(Purpose.EMBEDDING)
        embedding_dimension = config.embedding_dimension
        effective_model = model or config.model_id

        texts = [chunk.text_content for chunk in chunks]
        result = await provider.create_embedding(texts, model=effective_model)
        if len(result.embeddings) != len(chunks):
            raise ValueError(
                f"Embedding count mismatch: expected {len(chunks)}, got {len(result.embeddings)}"
            )

        with self.uow_factory() as uow:
            repo = EmbeddingRepository(uow.session, embedding_dimension=embedding_dimension)
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

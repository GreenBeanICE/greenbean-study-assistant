from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: str
    text_content: str
    score: float


class Retriever:
    def __init__(self, embedding_repository, chunk_repository) -> None:
        self.embedding_repository = embedding_repository
        self.chunk_repository = chunk_repository

    def retrieve(
        self,
        *,
        document_id: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        embeddings = self.embedding_repository.list_by_document(document_id)
        if not embeddings:
            return []

        scored: list[tuple[str, float]] = []
        for embedding in embeddings:
            if len(embedding.vector) != len(query_embedding):
                continue
            score = self._cosine_similarity(query_embedding, embedding.vector)
            scored.append((embedding.chunk_id, score))

        if not scored:
            return []

        scored.sort(key=lambda item: item[1], reverse=True)
        selected = scored[:top_k]
        score_by_chunk_id = {chunk_id: score for chunk_id, score in selected}
        chunks = self.chunk_repository.list_by_ids([chunk_id for chunk_id, _score in selected])
        return [
            RetrievalResult(
                chunk_id=chunk.id,
                text_content=chunk.text_content,
                score=score_by_chunk_id[chunk.id],
            )
            for chunk in chunks
            if chunk.id in score_by_chunk_id
        ]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = sqrt(sum(value * value for value in left))
        right_norm = sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

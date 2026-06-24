from datetime import datetime, timezone

from app.entities import Chunk
from app.rag.retriever import Retriever
from app.repositories.embedding_repository import ChunkEmbedding


class FakeEmbeddingRepository:
    def __init__(self, embeddings):
        self.embeddings = embeddings

    def list_by_document(self, document_id: str):
        return self.embeddings


class FakeChunkRepository:
    def __init__(self, chunks):
        self.chunks = chunks

    def list_by_ids(self, ids: list[str]):
        by_id = {chunk.id: chunk for chunk in self.chunks}
        return [by_id[chunk_id] for chunk_id in ids if chunk_id in by_id]


def test_retrieve_returns_top_k_sorted_by_score() -> None:
    embeddings = [
        ChunkEmbedding(
            id="e1",
            chunk_id="c1",
            embedding_model="m",
            vector_dimension=2,
            vector=[1.0, 0.0],
            created_at=datetime.now(timezone.utc),
        ),
        ChunkEmbedding(
            id="e2",
            chunk_id="c2",
            embedding_model="m",
            vector_dimension=2,
            vector=[0.0, 1.0],
            created_at=datetime.now(timezone.utc),
        ),
    ]
    chunks = [
        Chunk(id="c1", document_unit_id="u1", sequence_index=0, text_content="alpha"),
        Chunk(id="c2", document_unit_id="u1", sequence_index=1, text_content="beta"),
    ]
    retriever = Retriever(FakeEmbeddingRepository(embeddings), FakeChunkRepository(chunks))

    results = retriever.retrieve(document_id="doc-1", query_embedding=[1.0, 0.0], top_k=1)

    assert len(results) == 1
    assert results[0].chunk_id == "c1"
    assert results[0].text_content == "alpha"


def test_retrieve_returns_empty_when_index_is_empty() -> None:
    retriever = Retriever(FakeEmbeddingRepository([]), FakeChunkRepository([]))
    assert retriever.retrieve(document_id="doc-1", query_embedding=[1.0, 0.0], top_k=3) == []


def test_retrieve_skips_vectors_with_wrong_dimension() -> None:
    embeddings = [
        ChunkEmbedding(
            id="e1",
            chunk_id="c1",
            embedding_model="m",
            vector_dimension=3,
            vector=[1.0, 0.0, 0.0],
            created_at=datetime.now(timezone.utc),
        ),
        ChunkEmbedding(
            id="e2",
            chunk_id="c2",
            embedding_model="m",
            vector_dimension=2,
            vector=[0.5, 0.5],
            created_at=datetime.now(timezone.utc),
        ),
    ]
    chunks = [
        Chunk(id="c1", document_unit_id="u1", sequence_index=0, text_content="alpha"),
        Chunk(id="c2", document_unit_id="u1", sequence_index=1, text_content="beta"),
    ]
    retriever = Retriever(FakeEmbeddingRepository(embeddings), FakeChunkRepository(chunks))

    results = retriever.retrieve(document_id="doc-1", query_embedding=[1.0, 0.0], top_k=2)

    assert [result.chunk_id for result in results] == ["c2"]

"""RAG 检索器行为测试。"""

from dataclasses import dataclass

from app.rag.retriever import ChunkSearchResult, Retriever


@dataclass(frozen=True)
class FakeVectorIndex:
    results: list[ChunkSearchResult]

    def search(self, *, query_vector: list[float], top_k: int) -> list[ChunkSearchResult]:
        assert query_vector == [0.9, 0.1]
        assert top_k == 2
        return self.results


def test_retriever_returns_top_k_chunk_results_from_vector_index():
    expected = [
        ChunkSearchResult(
            chunk_id="chunk-1",
            document_unit_id="unit-1",
            text_content="相关内容 A",
            page_number=1,
            distance=0.01,
            metadata_json={"language": "zh"},
        ),
        ChunkSearchResult(
            chunk_id="chunk-2",
            document_unit_id="unit-2",
            text_content="relevant content B",
            page_number=2,
            distance=0.12,
            metadata_json={"language": "en"},
        ),
    ]
    retriever = Retriever(vector_index=FakeVectorIndex(expected))

    results = retriever.retrieve(query_vector=[0.9, 0.1], top_k=2)

    assert results == expected

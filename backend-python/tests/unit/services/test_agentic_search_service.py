"""最小 agentic search service 行为测试。"""

import pytest

from app.rag.retriever import ChunkSearchResult


class FakeEmbeddingService:
    def __init__(self):
        self.queries: list[str] = []

    async def embed_query(self, query: str) -> list[float]:
        self.queries.append(query)
        return [0.9, 0.1]


class FakeRetriever:
    def __init__(self, results: list[ChunkSearchResult]):
        self.results = results
        self.calls: list[dict] = []

    def retrieve(self, *, query_vector: list[float], top_k: int) -> list[ChunkSearchResult]:
        self.calls.append({"query_vector": query_vector, "top_k": top_k})
        return self.results


class FakeAgent:
    def __init__(self, output: dict):
        self.output = output
        self.calls: list[dict] = []

    async def generate_agentic_answer(
        self,
        *,
        question: str,
        retrieved_context,
        language: str,
        model_name: str | None,
        prompt_version: str,
    ) -> dict:
        self.calls.append(
            {
                "question": question,
                "retrieved_context": retrieved_context,
                "language": language,
                "model_name": model_name,
                "prompt_version": prompt_version,
            }
        )
        return self.output


class FakeSectionContextBuilder:
    def __init__(self):
        self.section_ids: list[str] = []

    def build_for_section(self, section_id: str):
        from app.rag.context_builder import SectionContext, SectionContextUnit

        self.section_ids.append(section_id)
        return SectionContext(
            section_id=section_id,
            document_id="doc-1",
            title="1.1 背景介绍",
            start_page=4,
            end_page=4,
            units=[
                SectionContextUnit(
                    document_unit_id="unit-section-1",
                    sequence_index=0,
                    page_number=4,
                    text_content="Section evidence text.",
                    metadata_json=None,
                )
            ],
            context_text="Section evidence text.",
        )


def valid_agentic_answer() -> dict:
    return {
        "status": "completed",
        "sentences": [
            {
                "id": "s1",
                "text": "AI 可以帮助学生定位课程资料中的关键证据。",
                "citations": [
                    {
                        "id": "c1",
                        "page": 2,
                        "document_unit_id": "unit-1",
                        "chunk_id": "chunk-1",
                        "source_text": "AI supports evidence lookup",
                        "start_char": 0,
                        "end_char": 27,
                    }
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_agentic_search_service_answers_query_with_citations_and_sources():
    from app.services.agentic_search_service import AgenticSearchService

    chunk_results = [
        ChunkSearchResult(
            chunk_id="chunk-1",
            document_unit_id="unit-1",
            text_content="AI supports evidence lookup in course documents.",
            page_number=2,
            distance=0.05,
            metadata_json={"section_id": "sec-1"},
        )
    ]
    embedding_service = FakeEmbeddingService()
    retriever = FakeRetriever(chunk_results)
    agent = FakeAgent(valid_agentic_answer())
    service = AgenticSearchService(
        embedding_service=embedding_service,
        retriever=retriever,
        answer_agent=agent,
    )

    result = await service.answer(
        query="AI 如何帮助学习？",
        language="zh",
        model_name=None,
        prompt_version="agentic-search-v1",
        top_k=3,
    )

    assert embedding_service.queries == ["AI 如何帮助学习？"]
    assert retriever.calls == [{"query_vector": [0.9, 0.1], "top_k": 3}]
    assert agent.calls[0]["retrieved_context"][0].chunk_id == "chunk-1"
    assert result["content_json"]["status"] == "completed"
    assert result["content_json"]["sentences"][0]["citations"][0]["chunk_id"] == "chunk-1"
    assert result["content_json"]["source_pages"] == [
        {
            "page": 2,
            "document_unit_id": "unit-1",
            "text": "AI supports evidence lookup in course documents.",
        }
    ]
    assert "AI 可以帮助学生定位课程资料中的关键证据。" in result["content_markdown"]


@pytest.mark.asyncio
async def test_agentic_search_service_rejects_completed_answer_without_citation():
    from app.services.agentic_search_service import AgenticSearchService

    invalid_answer = valid_agentic_answer()
    invalid_answer["sentences"][0]["citations"] = []
    service = AgenticSearchService(
        embedding_service=FakeEmbeddingService(),
        retriever=FakeRetriever([]),
        answer_agent=FakeAgent(invalid_answer),
    )

    with pytest.raises(ValueError, match="completed agentic answer requires citations"):
        await service.answer(query="无来源回答", language="zh")


@pytest.mark.asyncio
async def test_agentic_search_service_uses_section_context_when_only_section_id_is_given():
    from app.services.agentic_search_service import AgenticSearchService

    section_context_builder = FakeSectionContextBuilder()
    embedding_service = FakeEmbeddingService()
    retriever = FakeRetriever([])
    agent = FakeAgent(valid_agentic_answer())
    service = AgenticSearchService(
        embedding_service=embedding_service,
        retriever=retriever,
        answer_agent=agent,
        section_context_builder=section_context_builder,
    )

    result = await service.answer(section_id="sec-1", language="zh")

    assert section_context_builder.section_ids == ["sec-1"]
    assert embedding_service.queries == []
    assert retriever.calls == []
    assert agent.calls[0]["retrieved_context"][0].document_unit_id == "unit-section-1"
    assert result["section_id"] == "sec-1"
    assert result["content_json"]["source_pages"] == [
        {
            "page": 4,
            "document_unit_id": "unit-section-1",
            "text": "Section evidence text.",
        }
    ]

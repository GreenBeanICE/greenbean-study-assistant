"""最小 agentic search 服务：Embedding → Retriever → LLM → citations。"""

from typing import Protocol

from app.agents.analysis_agent import AnalysisAgent
from app.rag.context_builder import SectionContextBuilder
from app.rag.retriever import ChunkSearchResult
from app.schemas.analysis_schema import AgenticSearchOutput
from app.services.analysis_service import build_markdown_from_section_analysis


class QueryEmbeddingServiceProtocol(Protocol):
    async def embed_query(self, query: str) -> list[float]:
        """将用户问题转换为查询向量。"""


class RetrieverProtocol(Protocol):
    def retrieve(self, *, query_vector: list[float], top_k: int) -> list[ChunkSearchResult]:
        """按向量召回相关 chunks。"""


class AgenticAnswerAgentProtocol(Protocol):
    async def generate_agentic_answer(
        self,
        *,
        question: str,
        retrieved_context,
        language: str,
        model_name: str | None,
        prompt_version: str,
    ) -> dict:
        """基于召回上下文生成带 citations 的回答。"""


class AgenticSearchService:
    """最小可用 agentic search 编排服务。"""

    def __init__(
        self,
        *,
        embedding_service: QueryEmbeddingServiceProtocol,
        retriever: RetrieverProtocol,
        answer_agent: AgenticAnswerAgentProtocol | None = None,
        section_context_builder: SectionContextBuilder | None = None,
    ) -> None:
        self.embedding_service = embedding_service
        self.retriever = retriever
        self.answer_agent = answer_agent or AnalysisAgent()
        self.section_context_builder = section_context_builder

    async def answer(
        self,
        *,
        query: str | None = None,
        section_id: str | None = None,
        language: str = "zh",
        model_name: str | None = None,
        prompt_version: str = "agentic-search-v1",
        top_k: int = 5,
    ) -> dict:
        if not query and not section_id:
            raise ValueError("query or section_id is required")

        question = query or f"请解析小节 {section_id}"
        assert question is not None
        if query is None and section_id is not None and self.section_context_builder is not None:
            retrieved_context = self._retrieve_section_context(section_id)
        else:
            query_vector = await self.embedding_service.embed_query(question)
            retrieved_context = self.retriever.retrieve(query_vector=query_vector, top_k=top_k)
        raw_output = await self.answer_agent.generate_agentic_answer(
            question=question,
            retrieved_context=retrieved_context,
            language=language,
            model_name=model_name,
            prompt_version=prompt_version,
        )
        raw_output = self._with_retrieved_source_pages(raw_output, retrieved_context)
        if query is not None:
            raw_output.setdefault("query", query)
        if section_id is not None:
            raw_output.setdefault("section_id", section_id)
        validated_output = AgenticSearchOutput.model_validate(raw_output)
        content_json = validated_output.model_dump()
        return {
            "query": query,
            "section_id": section_id,
            "language": language,
            "content_markdown": build_markdown_from_section_analysis(content_json),
            "content_json": content_json,
            "model_name": model_name,
            "prompt_version": prompt_version,
        }

    def _retrieve_section_context(self, section_id: str) -> list[ChunkSearchResult]:
        assert self.section_context_builder is not None
        section_context = self.section_context_builder.build_for_section(section_id)
        return [
            ChunkSearchResult(
                chunk_id=f"section-unit:{unit.document_unit_id}",
                document_unit_id=unit.document_unit_id,
                text_content=unit.text_content,
                page_number=unit.page_number,
                distance=0.0,
                metadata_json={
                    "section_id": section_context.section_id,
                    "sequence_index": unit.sequence_index,
                },
            )
            for unit in section_context.units
        ]

    @staticmethod
    def _with_retrieved_source_pages(
        raw_output: dict,
        retrieved_context: list[ChunkSearchResult],
    ) -> dict:
        if raw_output.get("source_pages"):
            return raw_output
        output = dict(raw_output)
        seen: set[str] = set()
        source_pages = []
        for item in retrieved_context:
            if item.document_unit_id in seen:
                continue
            seen.add(item.document_unit_id)
            source_pages.append(
                {
                    "page": item.page_number,
                    "document_unit_id": item.document_unit_id,
                    "text": item.text_content,
                }
            )
        output["source_pages"] = source_pages
        return output

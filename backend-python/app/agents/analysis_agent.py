import json
from typing import Any, Dict

from app.prompts.analysis_prompts import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_PROMPT_TPL
from app.providers.registry import ProviderRegistry
from app.rag.context_builder import SectionContext
from app.rag.retriever import ChunkSearchResult
from app.schemas.analysis_schema import (
    AgenticSearchOutput,
    AnalysisOutput,
    SectionAnalysisOutput,
)


SECTION_ANALYSIS_SYSTEM_PROMPT = (
    "You generate section-level study analysis as strict JSON. "
    "Every completed analysis sentence must include source citations. "
    "Use only the provided section context as evidence."
)

SECTION_ANALYSIS_USER_PROMPT = """Analyze this document section.

Section ID: {section_id}
Section title: {section_title}
Output language: {language}

Return JSON with exactly this shape:
{{
  "section_id": "...",
  "section_title": "...",
  "status": "completed",
  "sentences": [
    {{
      "id": "s1",
      "text": "One analysis sentence.",
      "citations": [
        {{
          "id": "c1",
          "page": 1,
          "document_unit_id": "unit id",
          "chunk_id": null,
          "source_text": "exact supporting source text",
          "start_char": 0,
          "end_char": 10
        }}
      ]
    }}
  ],
  "source_pages": [
    {{
      "page": 1,
      "document_unit_id": "unit id",
      "text": "full text-version PDF page content"
    }}
  ]
}}

Context units:
{context_units}
"""

AGENTIC_SEARCH_SYSTEM_PROMPT = (
    "You answer study questions using retrieved course context as evidence. "
    "Return strict JSON. Every completed answer sentence must include citations."
)

AGENTIC_SEARCH_USER_PROMPT = """Question: {question}
Output language: {language}

Return JSON with this shape:
{{
  "query": "...",
  "section_id": null,
  "status": "completed",
  "sentences": [
    {{
      "id": "s1",
      "text": "One answer sentence.",
      "citations": [
        {{
          "id": "c1",
          "page": 1,
          "document_unit_id": "unit id",
          "chunk_id": "chunk id",
          "source_text": "exact supporting source text",
          "start_char": 0,
          "end_char": 10
        }}
      ]
    }}
  ],
  "source_pages": [
    {{
      "page": 1,
      "document_unit_id": "unit id",
      "text": "retrieved source text"
    }}
  ]
}}

Retrieved context:
{retrieved_context}
"""


class AnalysisAgent:
    async def generate_analysis(self, document_context: str) -> Dict[str, Any]:
        try:
            provider = ProviderRegistry.get_active()
            response = await provider.chat_completion(
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": ANALYSIS_USER_PROMPT_TPL.substitute(
                            document_context=document_context
                        ),
                    },
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            raw_content = response.content
            parsed = json.loads(raw_content)

            validated = AnalysisOutput.model_validate(parsed)
            return validated.model_dump()

        except json.JSONDecodeError as e:
            print(f"解析 JSON 失败, 大模型返回的原始内容为: {raw_content}")
            raise RuntimeError("大模型生成的格式不正确，请重试。") from e
        except Exception as e:
            print(f"生成解析时发生错误: {e}")
            raise e

    async def generate_section_analysis(
        self,
        *,
        section_context: SectionContext,
        language: str,
        model_name: str | None = None,
        prompt_version: str = "section-analysis-v1",
    ) -> Dict[str, Any]:
        del model_name, prompt_version
        context_units = "\n\n".join(
            (
                f"[document_unit_id={unit.document_unit_id}; page={unit.page_number}; "
                f"sequence_index={unit.sequence_index}]\n{unit.text_content}"
            )
            for unit in section_context.units
        )
        raw_content = ""
        try:
            provider = ProviderRegistry.get_active()
            response = await provider.chat_completion(
                messages=[
                    {"role": "system", "content": SECTION_ANALYSIS_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": SECTION_ANALYSIS_USER_PROMPT.format(
                            section_id=section_context.section_id,
                            section_title=section_context.title,
                            language=language,
                            context_units=context_units,
                        ),
                    },
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            raw_content = response.content
            parsed = json.loads(raw_content)
            validated = SectionAnalysisOutput.model_validate(parsed)
            return validated.model_dump()
        except json.JSONDecodeError as e:
            print(f"解析 JSON 失败, 大模型返回的原始内容为: {raw_content}")
            raise RuntimeError("大模型生成的小节解析格式不正确，请重试。") from e
        except Exception as e:
            print(f"生成小节解析时发生错误: {e}")
            raise e

    async def generate_agentic_answer(
        self,
        *,
        question: str,
        retrieved_context: list[ChunkSearchResult],
        language: str,
        model_name: str | None = None,
        prompt_version: str = "agentic-search-v1",
    ) -> Dict[str, Any]:
        del model_name, prompt_version
        context_text = "\n\n".join(
            (
                f"[chunk_id={item.chunk_id}; document_unit_id={item.document_unit_id}; "
                f"page={item.page_number}; distance={item.distance}]\n{item.text_content}"
            )
            for item in retrieved_context
        )
        raw_content = ""
        try:
            provider = ProviderRegistry.get_active()
            response = await provider.chat_completion(
                messages=[
                    {"role": "system", "content": AGENTIC_SEARCH_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": AGENTIC_SEARCH_USER_PROMPT.format(
                            question=question,
                            language=language,
                            retrieved_context=context_text,
                        ),
                    },
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            raw_content = response.content
            parsed = json.loads(raw_content)
            validated = AgenticSearchOutput.model_validate(parsed)
            return validated.model_dump()
        except json.JSONDecodeError as e:
            print(f"解析 JSON 失败, 大模型返回的原始内容为: {raw_content}")
            raise RuntimeError("大模型生成的检索回答格式不正确，请重试。") from e
        except Exception as e:
            print(f"生成检索回答时发生错误: {e}")
            raise e

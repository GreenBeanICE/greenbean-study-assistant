import json
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.entities import Chunk, DocumentRecord, Section
from app.providers.base import AIProvider
from app.services.chunk_service import FixedLengthChunker


AI_PROVIDER_NOT_CONFIGURED_REASON = "尚未配置 AI 模型服务"
PDF_OUTLINE_UNAVAILABLE_REASON = "未检测到可用的 PDF 自带目录"
SECTION_LINK_METADATA_FALLBACK = "metadata_fallback"


class OutlineCandidateValidationError(ValueError):
    pass


class OutlineCandidateService:
    """生成并校验 PDF outline / LLM outline 两套候选大纲。"""

    def build_candidates(
        self,
        *,
        document_id: str,
        page_index,
        pdf_outline: list[dict[str, Any]],
        chat_provider: AIProvider | None,
    ) -> dict[str, Any]:
        del chat_provider
        return {
            "page_index": self.page_index_summary(page_index),
            "outline_candidates": [
                self.build_pdf_outline_candidate(
                    document_id=document_id,
                    page_index=page_index,
                    pdf_outline=pdf_outline,
                ),
                self.unavailable_candidate(
                    source="llm_outline",
                    reason=AI_PROVIDER_NOT_CONFIGURED_REASON,
                ),
            ],
        }

    def build_pdf_outline_candidate(
        self,
        *,
        document_id: str,
        page_index,
        pdf_outline: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not pdf_outline:
            return self.unavailable_candidate(
                source="pdf_outline",
                reason=PDF_OUTLINE_UNAVAILABLE_REASON,
            )
        candidate = {
            "id": "pdf_outline",
            "document_id": document_id,
            "source": "pdf_outline",
            "status": "available",
            "reason": None,
            "sections": pdf_outline,
        }
        self.validate_candidate(candidate, page_index=page_index)
        return candidate

    async def build_llm_candidate(
        self,
        *,
        document_id: str,
        page_index,
        chat_provider: AIProvider | None,
    ) -> dict[str, Any]:
        if chat_provider is None:
            return self.unavailable_candidate(
                source="llm_outline",
                reason=AI_PROVIDER_NOT_CONFIGURED_REASON,
            )
        prompt = self._build_llm_outline_prompt(page_index)
        try:
            response = await chat_provider.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You generate document outline candidates as strict JSON. "
                            "Use only the provided text-version PDF pages."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(response.content)
            sections = parsed.get("sections", parsed)
            candidate = {
                "id": "llm_outline",
                "document_id": document_id,
                "source": "llm_outline",
                "status": "available",
                "reason": None,
                "sections": sections,
            }
            self.validate_candidate(candidate, page_index=page_index)
            return candidate
        except Exception as exc:
            return self.unavailable_candidate(
                source="llm_outline",
                reason=f"AI 大纲生成不可用: {exc}",
            )

    def validate_candidate(self, candidate: dict[str, Any], *, page_index) -> None:
        if candidate.get("status") != "available":
            return
        sections = candidate.get("sections")
        if not isinstance(sections, list) or not sections:
            raise OutlineCandidateValidationError("available outline candidate requires sections")

        page_numbers = {page.page_number for page in page_index.pages}
        if not page_numbers:
            raise OutlineCandidateValidationError("page index has no pages")
        min_page = min(page_numbers)
        max_page = max(page_numbers)
        temp_ids = {
            section.get("temp_id")
            for section in sections
            if isinstance(section.get("temp_id"), str)
        }
        for order, section in enumerate(sections):
            level = section.get("level")
            start_page = section.get("start_page")
            end_page = section.get("end_page")
            if not isinstance(level, int) or level < 1 or level > 6:
                raise OutlineCandidateValidationError("outline section level is invalid")
            if (
                not isinstance(start_page, int)
                or not isinstance(end_page, int)
                or start_page > end_page
                or start_page < min_page
                or end_page > max_page
            ):
                raise OutlineCandidateValidationError("outline section page range is invalid")
            if not any(start_page <= page <= end_page for page in page_numbers):
                raise OutlineCandidateValidationError("outline section maps to no DocumentUnit")
            parent_temp_id = section.get("parent_temp_id")
            if parent_temp_id is not None and parent_temp_id not in temp_ids:
                raise OutlineCandidateValidationError("outline section parent is invalid")
            section.setdefault("temp_id", f"{candidate['source']}-{order + 1}")
            section.setdefault("order_index", order)

    def page_index_summary(self, page_index) -> dict[str, Any]:
        return {
            "document_id": page_index.document_id,
            "page_count": page_index.page_count,
            "pages": [
                {
                    "document_id": page.document_id,
                    "document_unit_id": page.document_unit_id,
                    "page_number": page.page_number,
                    "sequence_index": page.sequence_index,
                    "text_content": page.text_content,
                    "char_count": page.char_count,
                    "metadata_json": page.metadata_json,
                    "parser_name": page.parser_name,
                    "parser_version": page.parser_version,
                }
                for page in page_index.pages
            ],
        }

    def unavailable_candidate(self, *, source: str, reason: str) -> dict[str, Any]:
        return {
            "id": source,
            "source": source,
            "status": "unavailable",
            "reason": reason,
            "sections": [],
        }

    def _build_llm_outline_prompt(self, page_index) -> str:
        page_text = "\n\n".join(
            (
                f"[page={page.page_number}; document_unit_id={page.document_unit_id}; "
                f"sequence_index={page.sequence_index}]\n{page.text_content}"
            )
            for page in page_index.pages
        )
        return f"""Create an outline candidate for this text-version PDF.

Return strict JSON:
{{
  "sections": [
    {{
      "temp_id": "s1",
      "title": "Section title",
      "level": 1,
      "parent_temp_id": null,
      "start_page": 1,
      "end_page": 1,
      "order_index": 0
    }}
  ]
}}

Pages:
{page_text}
"""


class OutlineConfirmationService:
    """把用户确认的候选大纲转成正式 Section，并生成可追溯 Chunk。"""

    def __init__(
        self,
        *,
        section_repository,
        document_unit_repository,
        chunk_repository,
        embedding_repository=None,
        vector_index_builder=None,
        chunk_size: int = 1200,
    ) -> None:
        self.section_repository = section_repository
        self.document_unit_repository = document_unit_repository
        self.chunk_repository = chunk_repository
        self.embedding_repository = embedding_repository
        self.vector_index_builder = vector_index_builder
        self.chunker = FixedLengthChunker(chunk_size=chunk_size)

    def confirm(
        self,
        *,
        document: DocumentRecord,
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        if candidate.get("status") != "available":
            raise OutlineCandidateValidationError("only available outline candidate can be confirmed")

        source = str(candidate.get("source") or candidate.get("id") or "outline")
        temp_to_section_id = {
            section["temp_id"]: self._stable_id(
                "section",
                document.id,
                source,
                str(section.get("temp_id") or section.get("order_index")),
            )
            for section in candidate.get("sections", [])
        }
        saved_sections: list[Section] = []
        chunks_by_id: dict[str, Chunk] = {}

        for order, item in enumerate(candidate.get("sections", [])):
            start_page = int(item["start_page"])
            end_page = int(item["end_page"])
            units = self.document_unit_repository.list_by_document_and_page_range(
                document_id=document.id,
                start_page=start_page,
                end_page=end_page,
            )
            section_id = temp_to_section_id[item["temp_id"]]
            section = Section(
                id=section_id,
                document_id=document.id,
                parent_section_id=temp_to_section_id.get(item.get("parent_temp_id")),
                title=str(item["title"]),
                level=int(item["level"]),
                order_index=int(item.get("order_index", order)),
                start_page=start_page,
                end_page=end_page,
                metadata_json={
                    "outline_source": source,
                    "candidate_temp_id": item["temp_id"],
                    "document_unit_ids": [unit.id for unit in units],
                    "section_unit_links_status": SECTION_LINK_METADATA_FALLBACK,
                },
                parser_name="OutlineConfirmationService",
                parser_version="0.1",
                external_id=item["temp_id"],
            )
            saved_sections.append(self.section_repository.save(section))
            for chunk in self.chunker.split_document_units(units):
                chunk_id = self._stable_id(
                    "chunk",
                    chunk.document_unit_id,
                    str(chunk.sequence_index),
                )
                metadata = dict(chunk.metadata_json or {})
                section_ids = list(metadata.get("section_ids", []))
                if section_id not in section_ids:
                    section_ids.append(section_id)
                metadata["section_ids"] = section_ids
                metadata["outline_source"] = source
                chunks_by_id[chunk_id] = chunk.model_copy(
                    update={"id": chunk_id, "metadata_json": metadata}
                )

        saved_chunks = [self.chunk_repository.save(chunk) for chunk in chunks_by_id.values()]
        return {
            "sections": saved_sections,
            "chunks": saved_chunks,
            "section_unit_links_status": SECTION_LINK_METADATA_FALLBACK,
            "chunk_status": "created" if saved_chunks else "empty",
            "embedding_status": "unavailable",
        }

    def _stable_id(self, *parts: str) -> str:
        return str(uuid5(NAMESPACE_URL, ":".join(parts)))

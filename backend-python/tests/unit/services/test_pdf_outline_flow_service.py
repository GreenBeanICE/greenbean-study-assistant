import pytest

from app.entities import DocumentRecord, DocumentUnit
from app.enums.document_file_type import DocumentFileType
from app.enums.document_status import DocumentStatus
from app.providers.base import ChatResult
from app.rag.page_index_builder import PageIndexBuilder
from app.services.section_service import (
    OutlineCandidateService,
    OutlineConfirmationService,
)


def _page(
    *,
    unit_id: str,
    document_id: str = "doc-1",
    page_number: int,
    text: str,
) -> DocumentUnit:
    return DocumentUnit(
        id=unit_id,
        document_id=document_id,
        sequence_index=page_number - 1,
        page_number=page_number,
        text_content=text,
        start_char=0,
        end_char=len(text),
        metadata_json={"source_type": "pdf"},
        parser_name="PDFParser",
        parser_version="1.0.0",
    )


class FakeSectionRepository:
    def __init__(self):
        self.saved = {}

    def save(self, section):
        self.saved[section.id] = section
        return section

    def list_by_document(self, document_id: str):
        return [
            section
            for section in self.saved.values()
            if section.document_id == document_id
        ]


class FakeDocumentUnitRepository:
    def __init__(self, units):
        self.units = units

    def list_by_document_and_page_range(self, *, document_id, start_page, end_page):
        return [
            unit
            for unit in self.units
            if unit.document_id == document_id
            and unit.page_number is not None
            and start_page <= unit.page_number <= end_page
        ]


class FakeChunkRepository:
    def __init__(self):
        self.saved = {}

    def save(self, chunk):
        self.saved[chunk.id] = chunk
        return chunk


class FakeChatProvider:
    async def chat_completion(self, **_kwargs):
        return ChatResult(
            content="""
            {
              "sections": [
                {
                  "temp_id": "ai-1",
                  "title": "AI 生成章节",
                  "level": 1,
                  "parent_temp_id": null,
                  "start_page": 1,
                  "end_page": 2,
                  "order_index": 0
                }
              ]
            }
            """
        )


def test_outline_candidates_share_page_index_and_report_unavailable_provider():
    units = [
        _page(unit_id="unit-1", page_number=1, text="第一页"),
        _page(unit_id="unit-2", page_number=2, text="第二页"),
    ]
    page_index = PageIndexBuilder().build_from_document_units(
        document_id="doc-1",
        document_units=units,
    )

    candidates = OutlineCandidateService().build_candidates(
        document_id="doc-1",
        page_index=page_index,
        pdf_outline=[],
        chat_provider=None,
    )

    assert candidates["page_index"]["page_count"] == 2
    assert [candidate["source"] for candidate in candidates["outline_candidates"]] == [
        "pdf_outline",
        "llm_outline",
    ]
    assert candidates["outline_candidates"][0]["status"] == "unavailable"
    assert candidates["outline_candidates"][0]["reason"] == "未检测到可用的 PDF 自带目录"
    assert candidates["outline_candidates"][1]["status"] == "unavailable"
    assert candidates["outline_candidates"][1]["reason"] == "尚未配置 AI 模型服务"


@pytest.mark.asyncio
async def test_llm_outline_candidate_is_validated_against_page_index():
    units = [
        _page(unit_id="unit-1", page_number=1, text="第一页"),
        _page(unit_id="unit-2", page_number=2, text="第二页"),
    ]
    page_index = PageIndexBuilder().build_from_document_units(
        document_id="doc-1",
        document_units=units,
    )

    candidate = await OutlineCandidateService().build_llm_candidate(
        document_id="doc-1",
        page_index=page_index,
        chat_provider=FakeChatProvider(),
    )

    assert candidate["source"] == "llm_outline"
    assert candidate["status"] == "available"
    assert candidate["sections"][0]["title"] == "AI 生成章节"
    assert candidate["sections"][0]["start_page"] == 1
    assert candidate["sections"][0]["end_page"] == 2


def test_confirm_outline_creates_idempotent_sections_and_traceable_chunks():
    document = DocumentRecord(
        id="doc-1",
        workspace_id="workspace-1",
        title="Cours",
        original_filename="cours.pdf",
        file_type=DocumentFileType.PDF,
        file_path="",
        status=DocumentStatus.PARSED,
        page_count=2,
    )
    units = [
        _page(unit_id="unit-1", page_number=1, text="ABCDE"),
        _page(unit_id="unit-2", page_number=2, text="FGHIJ"),
    ]
    section_repository = FakeSectionRepository()
    chunk_repository = FakeChunkRepository()
    service = OutlineConfirmationService(
        section_repository=section_repository,
        document_unit_repository=FakeDocumentUnitRepository(units),
        chunk_repository=chunk_repository,
        embedding_repository=None,
        vector_index_builder=None,
        chunk_size=3,
    )
    candidate = {
        "source": "pdf_outline",
        "status": "available",
        "sections": [
            {
                "temp_id": "pdf-1",
                "title": "Introduction",
                "level": 1,
                "parent_temp_id": None,
                "start_page": 1,
                "end_page": 2,
                "order_index": 0,
            }
        ],
    }

    first = service.confirm(
        document=document,
        candidate=candidate,
    )
    second = service.confirm(
        document=document,
        candidate=candidate,
    )

    assert [section.id for section in first["sections"]] == [
        section.id for section in second["sections"]
    ]
    assert len(section_repository.saved) == 1
    section = first["sections"][0]
    assert section.metadata_json["outline_source"] == "pdf_outline"
    assert section.metadata_json["document_unit_ids"] == ["unit-1", "unit-2"]
    assert first["section_unit_links_status"] == "metadata_fallback"
    assert first["embedding_status"] == "unavailable"
    assert chunk_repository.saved
    assert all(
        chunk.metadata_json["section_ids"] == [section.id]
        for chunk in chunk_repository.saved.values()
    )

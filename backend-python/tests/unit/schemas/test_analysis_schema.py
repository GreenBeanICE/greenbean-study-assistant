"""句子级可溯源小节解析 Schema 测试。"""

import pytest
from pydantic import ValidationError

from app.schemas.analysis_schema import SectionAnalysisOutput


def _valid_output_payload() -> dict:
    return {
        "section_id": "section-1",
        "section_title": "1.1 背景介绍",
        "status": "completed",
        "sentences": [
            {
                "id": "s1",
                "text": "人工智能正在改变教育资料的学习方式。",
                "citations": [
                    {
                        "id": "c1",
                        "page": 1,
                        "document_unit_id": "unit-1",
                        "chunk_id": "chunk-1",
                        "source_text": "人工智能技术取得了飞速发展。",
                        "start_char": 0,
                        "end_char": 14,
                    }
                ],
            }
        ],
        "source_pages": [
            {
                "page": 1,
                "document_unit_id": "unit-1",
                "text": "人工智能技术取得了飞速发展。",
            }
        ],
    }


def test_section_analysis_output_keeps_sentence_level_citations():
    output = SectionAnalysisOutput.model_validate(_valid_output_payload())

    assert output.status == "completed"
    assert output.sentences[0].text == "人工智能正在改变教育资料的学习方式。"
    assert output.sentences[0].citations[0].page == 1
    assert output.sentences[0].citations[0].start_char == 0
    assert output.sentences[0].citations[0].end_char == 14
    assert output.source_pages[0].text == "人工智能技术取得了飞速发展。"


def test_completed_section_analysis_rejects_sentence_without_citation():
    payload = _valid_output_payload()
    payload["sentences"][0]["citations"] = []

    with pytest.raises(ValidationError, match="completed"):
        SectionAnalysisOutput.model_validate(payload)


def test_draft_section_analysis_allows_uncited_sentence_for_review():
    payload = _valid_output_payload()
    payload["status"] = "draft"
    payload["sentences"][0]["citations"] = []

    output = SectionAnalysisOutput.model_validate(payload)

    assert output.status == "draft"
    assert output.sentences[0].citations == []

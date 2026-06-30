from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.analysis_agent import AnalysisAgent
from app.providers.base import ChatResult
from app.providers.registry import ProviderNotFoundError


@patch("app.agents.analysis_agent.ProviderRegistry")
@pytest.mark.asyncio
async def test_generate_analysis_success(MockRegistry):
    mock_provider = MagicMock()
    mock_provider.chat_completion = AsyncMock(return_value=ChatResult(content="""{
        "summary": "本节主要介绍了数据库第三范式的核心定义。",
        "key_concepts": ["3NF", "传递函数依赖"],
        "terms": [{"fr": "3NF", "zh": "第三范式", "explanation": "消除传递依赖"}],
        "highlights": ["重点是理解传递依赖"],
        "source_refs": [{"page": 5, "title": "Normalisation"}]
    }"""))
    MockRegistry.get_active.return_value = mock_provider

    agent = AnalysisAgent()
    result = await agent.generate_analysis("Chaque déterminant non clé doit être une clé primaire...")

    assert isinstance(result, dict)
    assert result["summary"] == "本节主要介绍了数据库第三范式的核心定义。"
    assert "3NF" in result["key_concepts"]
    assert result["terms"][0]["fr"] == "3NF"

    mock_provider.chat_completion.assert_called_once()
    called_kwargs = mock_provider.chat_completion.call_args[1]
    assert called_kwargs["response_format"] == {"type": "json_object"}
    assert called_kwargs["temperature"] == 0.3


@patch("app.agents.analysis_agent.ProviderRegistry")
@pytest.mark.asyncio
async def test_generate_analysis_json_error(MockRegistry):
    mock_provider = MagicMock()
    mock_provider.chat_completion = AsyncMock(return_value=ChatResult(content='{"summary": "残缺的JSON"'))
    MockRegistry.get_active.return_value = mock_provider

    agent = AnalysisAgent()

    with pytest.raises(RuntimeError) as exc_info:
        await agent.generate_analysis("Some context")

    assert "大模型生成的格式不正确" in str(exc_info.value)


def test_analysis_agent_requires_active_provider():
    agent = AnalysisAgent()
    with pytest.raises(ProviderNotFoundError):
        import asyncio
        asyncio.run(agent.generate_analysis("test"))


# ── analysis_service.py ──────────────────────────────────────────────

def test_build_markdown_from_json():
    from app.services.analysis_service import build_markdown_from_json
    data = {
        "summary": "测试总结",
        "key_concepts": ["概念A", "概念B"],
        "terms": [{"fr": "Terme1", "zh": "术语1", "explanation": "解释1"}],
        "highlights": ["要点1"],
    }
    md = build_markdown_from_json(data)
    assert "测试总结" in md
    assert "概念A" in md
    assert "Terme1" in md
    assert "术语1" in md
    assert "要点1" in md


@patch("app.services.analysis_service.AnalysisAgent")
@pytest.mark.asyncio
async def test_process_and_save_analysis(MockAgent):
    from app.services.analysis_service import process_and_save_analysis
    mock_agent = MockAgent.return_value
    mock_agent.generate_analysis = AsyncMock(return_value={
        "summary": "test", "key_concepts": [], "terms": [], "highlights": [],
    })
    result = await process_and_save_analysis("doc-1", "sec-1", "ctx")
    assert result.document_id == "doc-1"
    assert result.section_id == "sec-1"
    assert result.analysis_type.value == "section"


class FakeSectionContextBuilder:
    def build_for_section(self, section_id: str):
        from app.rag.context_builder import SectionContext, SectionContextUnit

        assert section_id == "sec-1"
        return SectionContext(
            section_id="sec-1",
            document_id="doc-1",
            title="1.1 背景介绍",
            start_page=1,
            end_page=1,
            units=[
                SectionContextUnit(
                    document_unit_id="unit-1",
                    sequence_index=0,
                    page_number=1,
                    text_content="近年来，人工智能技术取得了飞速发展。",
                    metadata_json=None,
                )
            ],
            context_text="近年来，人工智能技术取得了飞速发展。",
        )


class FakeSectionAnalysisAgent:
    def __init__(self, output: dict):
        self.output = output
        self.calls: list[dict] = []

    async def generate_section_analysis(
        self,
        *,
        section_context,
        language: str,
        model_name: str | None,
        prompt_version: str,
    ) -> dict:
        self.calls.append(
            {
                "section_context": section_context,
                "language": language,
                "model_name": model_name,
                "prompt_version": prompt_version,
            }
        )
        return self.output


class FakeAnalysisResultRepository:
    def __init__(self):
        self.saved = []

    def save(self, result):
        self.saved.append(result)
        return result


def valid_section_analysis_output() -> dict:
    return {
        "section_id": "sec-1",
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
                        "source_text": "人工智能技术取得了飞速发展",
                        "start_char": 3,
                        "end_char": 17,
                    }
                ],
            }
        ],
        "source_pages": [
            {
                "page": 1,
                "document_unit_id": "unit-1",
                "text": "近年来，人工智能技术取得了飞速发展。",
            }
        ],
    }


@pytest.mark.asyncio
async def test_section_analysis_service_returns_traceable_analysis_result():
    from app.enums.analysis_type import AnalysisType
    from app.services.analysis_service import SectionAnalysisService

    agent = FakeSectionAnalysisAgent(valid_section_analysis_output())
    repository = FakeAnalysisResultRepository()
    service = SectionAnalysisService(
        context_builder=FakeSectionContextBuilder(),
        analysis_agent=agent,
        analysis_result_repository=repository,
    )

    result = await service.analyze_section(
        section_id="sec-1",
        language="zh",
        model_name="gemini-embedding-compatible-chat",
        prompt_version="section-analysis-v1",
    )

    assert result.document_id == "doc-1"
    assert result.section_id == "sec-1"
    assert result.analysis_type == AnalysisType.SECTION
    assert result.language == "zh"
    assert result.prompt_version == "section-analysis-v1"
    assert result.content_json["status"] == "completed"
    assert result.content_json["sentences"][0]["citations"][0]["document_unit_id"] == "unit-1"
    assert result.content_json["source_pages"][0]["text"] == "近年来，人工智能技术取得了飞速发展。"
    assert "人工智能正在改变教育资料的学习方式。" in result.content_markdown
    assert repository.saved == [result]
    assert agent.calls[0]["section_context"].section_id == "sec-1"


@pytest.mark.asyncio
async def test_section_analysis_service_rejects_completed_sentence_without_citation():
    from app.services.analysis_service import SectionAnalysisService

    invalid_output = valid_section_analysis_output()
    invalid_output["sentences"][0]["citations"] = []
    repository = FakeAnalysisResultRepository()
    service = SectionAnalysisService(
        context_builder=FakeSectionContextBuilder(),
        analysis_agent=FakeSectionAnalysisAgent(invalid_output),
        analysis_result_repository=repository,
    )

    with pytest.raises(ValueError, match="completed section analysis requires citations"):
        await service.analyze_section(
            section_id="sec-1",
            language="zh",
            model_name=None,
            prompt_version="section-analysis-v1",
        )

    assert repository.saved == []

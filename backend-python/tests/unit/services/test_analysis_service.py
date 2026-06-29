from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.analysis_agent import AnalysisAgent
from app.entities.analysis_result import AnalysisResult
from app.enums.analysis_type import AnalysisType
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
    MockRegistry.get_active_chat.return_value = mock_provider

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
    MockRegistry.get_active_chat.return_value = mock_provider

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


# ── AnalysisService.generate_section_analysis ───────────────────────


@pytest.mark.asyncio
async def test_generate_section_analysis_uses_raw_units_only():
    from app.services.analysis_service import AnalysisService

    section_service = MagicMock()
    section_service.get_section_content.return_value = {
        "anchor_unit_id": "u1",
        "units": [
            SimpleNamespace(id="u1", sequence_index=0, page_number=3, text_content="第一段原文"),
            SimpleNamespace(id="u2", sequence_index=1, page_number=4, text_content="第二段原文"),
        ],
    }
    section_service.get_section_by_id.return_value = SimpleNamespace(
        id="sec-1",
        document_id="doc-1",
        title="1.1 背景介绍",
    )
    agent = MagicMock()
    agent.generate_analysis = AsyncMock(
        return_value={
            "summary": "摘要",
            "key_concepts": ["概念 A"],
            "terms": [],
            "highlights": ["重点 A"],
            "source_refs": [{"page": 3, "title": "1.1 背景介绍"}],
        }
    )
    service = AnalysisService(
        section_service=section_service,
        analysis_agent=agent,
        uow_factory=None,
    )

    result = await service.generate_section_analysis("sec-1")

    assert isinstance(result, AnalysisResult)
    assert result.document_id == "doc-1"
    assert result.section_id == "sec-1"
    assert result.analysis_type == AnalysisType.SECTION
    called_context = agent.generate_analysis.await_args.args[0]
    assert "第一段原文" in called_context
    assert "第二段原文" in called_context
    assert "chat_messages" not in called_context
    assert "analyses" not in called_context


@pytest.mark.asyncio
async def test_generate_section_analysis_rejects_empty_units():
    from app.services.analysis_service import AnalysisService

    section_service = MagicMock()
    section_service.get_section_content.return_value = {
        "anchor_unit_id": None,
        "units": [],
    }
    section_service.get_section_by_id.return_value = SimpleNamespace(
        id="sec-1",
        document_id="doc-1",
        title="1.1 背景介绍",
    )
    service = AnalysisService(
        section_service=section_service,
        analysis_agent=MagicMock(),
        uow_factory=None,
    )

    with pytest.raises(ValueError) as exc_info:
        await service.generate_section_analysis("sec-1")

    assert "资料依据不足" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_section_analysis_persists_generated_result():
    from app.services.analysis_service import AnalysisService

    section_service = MagicMock()
    section_service.get_section_by_id.return_value = SimpleNamespace(
        id="sec-1",
        document_id="doc-1",
        title="1.1 背景介绍",
    )
    section_service.get_section_content.return_value = {
        "anchor_unit_id": "u1",
        "units": [
            SimpleNamespace(
                id="u1",
                sequence_index=0,
                page_number=3,
                text_content="第一段原文",
            )
        ],
    }
    agent = MagicMock()
    agent.generate_analysis = AsyncMock(
        return_value={
            "summary": "摘要",
            "key_concepts": [],
            "terms": [],
            "highlights": [],
            "source_refs": [],
        }
    )

    class FakeRepo:
        saved = None

        def __init__(self, _session):
            pass

        def get_by_section_id(self, _section_id):
            return None

        def save(self, result):
            type(self).saved = result
            return result

    class FakeUow:
        def __init__(self):
            self.session = object()
            self.committed = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def commit(self):
            self.committed = True

    fake_uow = FakeUow()

    with patch(
        "app.repositories.analysis_result_repository.AnalysisResultRepository",
        FakeRepo,
    ):
        service = AnalysisService(
            section_service=section_service,
            analysis_agent=agent,
            uow_factory=lambda: fake_uow,
        )

        result = await service.generate_section_analysis("sec-1")

    assert isinstance(result, AnalysisResult)
    assert FakeRepo.saved is not None
    assert FakeRepo.saved.section_id == "sec-1"
    assert fake_uow.committed is True

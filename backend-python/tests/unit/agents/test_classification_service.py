from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.classification_agent import RouterAgent
from app.providers.base import ChatResult


@patch("app.agents.classification_agent.ProviderRegistry")
@pytest.mark.asyncio
async def test_classification_tests_with_mock(MockRegistry):
    mock_provider = MagicMock()
    mock_provider.chat_completion = AsyncMock(
        return_value=ChatResult(
            content='{"route": "CONCEPT", "reason": "这是 Mock 测试模拟的判决理由"}'
        )
    )
    MockRegistry.get_active.return_value = mock_provider

    agent = RouterAgent()

    test_cases = [
        "这份课件分成哪几部分？",
        "第 3 页主要讲什么？",
        "clé étrangère 是什么意思？",
        "解释一下 normalisation",
        "数据库设计这一章有哪些重点概念？",
        "Peux-tu m'expliquer ce qu'est un polymorphisme ?",
    ]

    for question in test_cases:
        decision = await agent.route_question(question)
        assert decision.route == "CONCEPT"
        assert "模拟的判决理由" in decision.reason

    assert mock_provider.chat_completion.call_count == len(test_cases)


@patch("app.agents.classification_agent.ProviderRegistry")
@pytest.mark.asyncio
async def test_classification_falls_back_when_model_call_fails(MockRegistry):
    mock_provider = MagicMock()
    mock_provider.chat_completion.side_effect = RuntimeError("model unavailable")
    MockRegistry.get_active.return_value = mock_provider

    agent = RouterAgent()
    decision = await agent.route_question("这份课件主要讲什么？")

    assert decision.route == "COMPREHENSIVE"
    assert "model unavailable" in decision.reason

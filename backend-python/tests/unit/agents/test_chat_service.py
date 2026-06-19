from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.base import ChatResult
from app.schemas.chat_schema import ChatRequest, ChatResponse


@patch("app.agents.chat_agent.ProviderRegistry")
@patch("app.agents.classification_agent.ProviderRegistry")
@pytest.mark.asyncio
async def test_chat_agent_with_mock(MockClassifyRegistry, MockChatRegistry):
    mock_router_decision = MagicMock()
    mock_router_decision.route = "CONCEPT"

    mock_router_provider = MagicMock()
    mock_router_provider.chat_completion = AsyncMock(
        return_value=ChatResult(
            content='{"route": "CONCEPT", "reason": "test"}'
        )
    )
    MockClassifyRegistry.get_active.return_value = mock_router_provider

    mock_chat_provider = MagicMock()
    mock_chat_provider.chat_completion = AsyncMock(
        return_value=ChatResult(
            content="中法双语回复：这是一个Mock测试。\nExplication : C'est un test mock."
        )
    )
    MockChatRegistry.get_active.return_value = mock_chat_provider

    from app.agents.chat_agent import ChatAgent
    agent = ChatAgent()

    request = ChatRequest(
        session_id="test-session-1",
        query="Explique-moi le mock",
        history=[{"role": "user", "content": "Bonjour"}],
    )

    response = await agent.generate_response(request)

    assert "这是一个Mock测试。" in response.answer
    assert isinstance(response, ChatResponse)
    assert response.session_id == "test-session-1"

    mock_chat_provider.chat_completion.assert_called_once()

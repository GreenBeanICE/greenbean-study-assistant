from unittest.mock import AsyncMock, patch

import pytest

from app.providers.base import ChatResult
from app.providers.openai_compat_provider import OpenAICompatibleProvider


class TestOpenAICompatibleProvider:
    def test_initializes_with_config(self, provider_config_factory):
        provider = OpenAICompatibleProvider(provider_config_factory())
        assert provider.config.name == "test-cfg"

    @patch("app.providers.openai_compat_provider.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_chat_completion_returns_content(
        self, MockAsyncOpenAI, provider_config_factory
    ):
        mock_client = MockAsyncOpenAI.return_value
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="Hello"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = OpenAICompatibleProvider(provider_config_factory())
        result = await provider.chat_completion(
            messages=[{"role": "user", "content": "hi"}]
        )
        assert isinstance(result, ChatResult)
        assert result.content == "Hello"

    @patch("app.providers.openai_compat_provider.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_chat_completion_passes_model_and_params(
        self, MockAsyncOpenAI, provider_config_factory
    ):
        mock_client = MockAsyncOpenAI.return_value
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="OK"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = OpenAICompatibleProvider(provider_config_factory())
        await provider.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            model="override-model",
            temperature=0.5,
            max_tokens=100,
            response_format={"type": "json_object"},
        )
        kwargs = mock_client.chat.completions.create.call_args[1]
        assert kwargs["model"] == "override-model"
        assert kwargs["temperature"] == 0.5
        assert kwargs["max_tokens"] == 100
        assert kwargs["response_format"] == {"type": "json_object"}

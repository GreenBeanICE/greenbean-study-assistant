from unittest.mock import AsyncMock, patch

import pytest

from app.enums.api_mode import ApiMode
from app.entities.provider_config import ProviderConfig
from app.providers.base import ChatResult


class TestOpenAICompatibleProvider:
    def test_provider_initializes_with_config(self):
        config = ProviderConfig(
            name="test",
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-test",
            api_host="https://api.deepseek.com",
            model_id="deepseek-chat",
            display_name="Test",
        )
        from app.providers.openai_compat_provider import OpenAICompatibleProvider
        provider = OpenAICompatibleProvider(config)
        assert provider.config.name == "test"

    @patch("app.providers.openai_compat_provider.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_chat_completion_returns_content(self, MockAsyncOpenAI):
        mock_client = MockAsyncOpenAI.return_value
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="Hello from LLM"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        config = ProviderConfig(
            name="test",
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-test",
            api_host="https://api.test.com",
            model_id="test-model",
            display_name="Test",
        )
        from app.providers.openai_compat_provider import OpenAICompatibleProvider
        provider = OpenAICompatibleProvider(config)

        result = await provider.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
        )

        assert isinstance(result, ChatResult)
        assert result.content == "Hello from LLM"

    @patch("app.providers.openai_compat_provider.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_chat_completion_passes_model_and_params(self, MockAsyncOpenAI):
        mock_client = MockAsyncOpenAI.return_value
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="OK"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        config = ProviderConfig(
            name="test",
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-test",
            api_host="https://api.test.com",
            model_id="default-model",
            display_name="Test",
        )
        from app.providers.openai_compat_provider import OpenAICompatibleProvider
        provider = OpenAICompatibleProvider(config)

        await provider.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            model="override-model",
            temperature=0.5,
            max_tokens=100,
            response_format={"type": "json_object"},
        )

        mock_client.chat.completions.create.assert_called_once()
        kwargs = mock_client.chat.completions.create.call_args[1]
        assert kwargs["model"] == "override-model"
        assert kwargs["temperature"] == 0.5
        assert kwargs["max_tokens"] == 100
        assert kwargs["response_format"] == {"type": "json_object"}

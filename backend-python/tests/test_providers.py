from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.providers.base import ChatResult
from app.providers.openai_compat_provider import OpenAICompatibleProvider
from app.providers.registry import ProviderNotFoundError, ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository
from app.services.provider_service import ProviderService


def make_config(name: str = "test-cfg", is_active: bool = False) -> ProviderConfig:
    return ProviderConfig(
        name=name, api_mode=ApiMode.OPENAI_COMPAT, api_key="sk-test",
        api_host="https://api.test.com", model_id="test-model",
        display_name=name, is_active=is_active,
    )


# ── Registry ─────────────────────────────────────────────────────────

class TestProviderRegistry:
    def setup_method(self):
        ProviderRegistry.clear()

    def test_build_openai_compat_provider(self):
        config = make_config(name="test-deepseek")
        provider = ProviderRegistry.build_provider(config)
        assert isinstance(provider, OpenAICompatibleProvider)

    def test_activate_and_get_active(self):
        config = make_config(name="test-openai", is_active=True)
        provider = ProviderRegistry.activate(config)
        assert ProviderRegistry.get_active() is provider
        assert ProviderRegistry.get_active_config().name == "test-openai"

    def test_get_active_raises_when_none_activated(self):
        ProviderRegistry.clear()
        with pytest.raises(ProviderNotFoundError, match="当前没有激活的 provider"):
            ProviderRegistry.get_active()

    def test_activate_replaces_previous(self):
        ProviderRegistry.activate(make_config(name="a"))
        ProviderRegistry.activate(make_config(name="b"))
        assert ProviderRegistry.get_active_config().name == "b"

    def test_clear_resets_active(self):
        ProviderRegistry.activate(make_config(name="t"))
        ProviderRegistry.clear()
        with pytest.raises(ProviderNotFoundError):
            ProviderRegistry.get_active()

    def test_unsupported_api_mode_raises(self):
        config = ProviderConfig.model_construct(
            name="bad", api_mode="unsupported-mode", api_key="sk-test",
            api_host="https://test.com", model_id="test", display_name="Bad",
        )
        with pytest.raises(ValueError, match="不支持的 API 模式"):
            ProviderRegistry.build_provider(config)


# ── Provider Implementation ──────────────────────────────────────────

class TestOpenAICompatibleProvider:
    def test_initializes_with_config(self):
        provider = OpenAICompatibleProvider(make_config())
        assert provider.config.name == "test-cfg"

    @patch("app.providers.openai_compat_provider.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_chat_completion_returns_content(self, MockAsyncOpenAI):
        mock_client = MockAsyncOpenAI.return_value
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="Hello"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = OpenAICompatibleProvider(make_config())
        result = await provider.chat_completion(messages=[{"role": "user", "content": "hi"}])
        assert isinstance(result, ChatResult)
        assert result.content == "Hello"

    @patch("app.providers.openai_compat_provider.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_chat_completion_passes_model_and_params(self, MockAsyncOpenAI):
        mock_client = MockAsyncOpenAI.return_value
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="OK"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = OpenAICompatibleProvider(make_config())
        await provider.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            model="override-model", temperature=0.5, max_tokens=100,
            response_format={"type": "json_object"},
        )
        kwargs = mock_client.chat.completions.create.call_args[1]
        assert kwargs["model"] == "override-model"
        assert kwargs["temperature"] == 0.5
        assert kwargs["max_tokens"] == 100
        assert kwargs["response_format"] == {"type": "json_object"}


# ── Service ──────────────────────────────────────────────────────────

class TestProviderService:
    @pytest.fixture
    def mock_uow(self):
        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.__exit__.return_value = None
        uow.session = MagicMock()
        return uow

    def test_create(self, mock_uow):
        service = ProviderService(uow=mock_uow)
        result = service.create(dict(
            name="new-cfg", api_mode=ApiMode.OPENAI_COMPAT, api_key="sk-new",
            api_host="https://api.new.com", model_id="new-model", display_name="New",
        ))
        assert result.name == "new-cfg"
        mock_uow.commit.assert_called_once()

    def test_get_by_id(self, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=make_config()):
            assert ProviderService(uow=mock_uow).get_by_id("some-id").name == "test-cfg"

    def test_get_by_id_returns_none(self, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=None):
            assert ProviderService(uow=mock_uow).get_by_id("missing") is None

    def test_list_all(self, mock_uow):
        with patch.object(ProviderConfigRepository, "list_all", return_value=[make_config()]):
            assert len(ProviderService(uow=mock_uow).list_all()) == 1

    def test_delete(self, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=make_config()):
            with patch.object(ProviderConfigRepository, "delete", return_value=True):
                assert ProviderService(uow=mock_uow).delete("some-id") is True

    def test_delete_nonexistent(self, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=None):
            assert ProviderService(uow=mock_uow).delete("missing") is False

    @patch("app.services.provider_service.ProviderRegistry")
    def test_activate(self, MockRegistry, mock_uow):
        config = make_config(name="to-activate")
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=config):
            with patch.object(ProviderConfigRepository, "save"):
                with patch.object(ProviderConfigRepository, "deactivate_all"):
                    result = ProviderService(uow=mock_uow).activate("some-id")
                    assert result.is_active is True
                    MockRegistry.activate.assert_called_once_with(config)

    @patch("app.services.provider_service.ProviderRegistry")
    def test_activate_nonexistent(self, MockRegistry, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=None):
            assert ProviderService(uow=mock_uow).activate("missing") is None
            MockRegistry.activate.assert_not_called()

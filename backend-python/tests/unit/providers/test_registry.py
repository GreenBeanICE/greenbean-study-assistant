import pytest

from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.providers.openai_compat_provider import OpenAICompatibleProvider
from app.providers.registry import ProviderNotFoundError, ProviderRegistry


class TestProviderRegistry:
    def setup_method(self):
        ProviderRegistry.clear()

    def test_build_openai_compat_provider(self, provider_config_factory):
        config = provider_config_factory(name="test-deepseek")
        provider = ProviderRegistry.build_provider(config)
        assert isinstance(provider, OpenAICompatibleProvider)

    def test_activate_chat_routes_to_chat_slot(self, provider_config_factory):
        config = provider_config_factory(name="chat-cfg", purpose=Purpose.CHAT)
        provider = ProviderRegistry.activate(config)
        assert ProviderRegistry.get_active_chat() is provider
        assert ProviderRegistry.get_active_config(Purpose.CHAT).name == "chat-cfg"

    def test_activate_embedding_routes_to_embedding_slot(self, provider_config_factory):
        config = provider_config_factory(
            name="embed-cfg", purpose=Purpose.EMBEDDING, embedding_dimension=1024
        )
        ProviderRegistry.activate(config)
        assert ProviderRegistry.get_active_embedding() is not None
        assert ProviderRegistry.get_active_config(Purpose.EMBEDDING).name == "embed-cfg"

    def test_chat_and_embedding_are_independent(self, provider_config_factory):
        chat = provider_config_factory(name="c", purpose=Purpose.CHAT)
        embed = provider_config_factory(
            name="e", purpose=Purpose.EMBEDDING, embedding_dimension=8
        )
        ProviderRegistry.activate(chat)
        ProviderRegistry.activate(embed)
        assert ProviderRegistry.get_active_config(Purpose.CHAT).name == "c"
        assert ProviderRegistry.get_active_config(Purpose.EMBEDDING).name == "e"

    def test_get_active_chat_raises_when_none(self):
        with pytest.raises(ProviderNotFoundError, match="chat provider"):
            ProviderRegistry.get_active_chat()

    def test_get_active_embedding_raises_when_none(self):
        with pytest.raises(ProviderNotFoundError, match="embedding provider"):
            ProviderRegistry.get_active_embedding()

    def test_clear_purpose_only(self, provider_config_factory):
        ProviderRegistry.activate(provider_config_factory(name="c", purpose=Purpose.CHAT))
        ProviderRegistry.activate(
            provider_config_factory(name="e", purpose=Purpose.EMBEDDING, embedding_dimension=8)
        )
        ProviderRegistry.clear(Purpose.CHAT)
        with pytest.raises(ProviderNotFoundError):
            ProviderRegistry.get_active_chat()
        assert ProviderRegistry.get_active_embedding() is not None

    def test_clear_all(self, provider_config_factory):
        ProviderRegistry.activate(provider_config_factory(name="c", purpose=Purpose.CHAT))
        ProviderRegistry.clear()
        with pytest.raises(ProviderNotFoundError):
            ProviderRegistry.get_active_chat()

    def test_unsupported_api_mode_raises(self):
        config = ProviderConfig.model_construct(
            name="bad",
            api_mode="unsupported-mode",
            api_key="sk-test",
            api_host="https://test.com",
            model_id="test",
            display_name="Bad",
            purpose=Purpose.CHAT,
        )
        with pytest.raises(ValueError, match="不支持的 API 模式"):
            ProviderRegistry.build_provider(config)

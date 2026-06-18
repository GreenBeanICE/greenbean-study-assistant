import pytest

from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.providers.openai_compat_provider import OpenAICompatibleProvider
from app.providers.registry import ProviderNotFoundError, ProviderRegistry


class TestProviderRegistry:
    def setup_method(self):
        ProviderRegistry.clear()

    def test_build_openai_compat_provider(self, provider_config_factory):
        config = provider_config_factory(name="test-deepseek")
        provider = ProviderRegistry.build_provider(config)
        assert isinstance(provider, OpenAICompatibleProvider)

    def test_activate_and_get_active(self, provider_config_factory):
        config = provider_config_factory(name="test-openai", is_active=True)
        provider = ProviderRegistry.activate(config)
        assert ProviderRegistry.get_active() is provider
        assert ProviderRegistry.get_active_config().name == "test-openai"

    def test_get_active_raises_when_none_activated(self):
        ProviderRegistry.clear()
        with pytest.raises(ProviderNotFoundError, match="当前没有激活的 provider"):
            ProviderRegistry.get_active()

    def test_activate_replaces_previous(self, provider_config_factory):
        ProviderRegistry.activate(provider_config_factory(name="a"))
        ProviderRegistry.activate(provider_config_factory(name="b"))
        assert ProviderRegistry.get_active_config().name == "b"

    def test_clear_resets_active(self, provider_config_factory):
        ProviderRegistry.activate(provider_config_factory(name="t"))
        ProviderRegistry.clear()
        with pytest.raises(ProviderNotFoundError):
            ProviderRegistry.get_active()

    def test_unsupported_api_mode_raises(self):
        config = ProviderConfig.model_construct(
            name="bad",
            api_mode="unsupported-mode",
            api_key="sk-test",
            api_host="https://test.com",
            model_id="test",
            display_name="Bad",
        )
        with pytest.raises(ValueError, match="不支持的 API 模式"):
            ProviderRegistry.build_provider(config)

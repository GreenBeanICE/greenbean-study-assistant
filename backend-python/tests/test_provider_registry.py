import pytest

from app.enums.api_mode import ApiMode
from app.entities.provider_config import ProviderConfig
from app.providers.openai_compat_provider import OpenAICompatibleProvider
from app.providers.registry import ProviderRegistry, ProviderNotFoundError


class TestProviderRegistry:
    def setup_method(self):
        ProviderRegistry.clear()

    def test_build_openai_compat_provider(self):
        config = ProviderConfig(
            name="test-deepseek",
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-test",
            api_host="https://api.deepseek.com",
            model_id="deepseek-chat",
            display_name="Test DeepSeek",
        )
        provider = ProviderRegistry.build_provider(config)
        assert isinstance(provider, OpenAICompatibleProvider)

    def test_activate_and_get_active(self):
        config = ProviderConfig(
            name="test-openai",
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-test",
            api_host="https://api.openai.com",
            model_id="gpt-4o",
            display_name="Test OpenAI",
        )
        provider = ProviderRegistry.activate(config)
        assert isinstance(provider, OpenAICompatibleProvider)

        active = ProviderRegistry.get_active()
        assert active is provider

        active_config = ProviderRegistry.get_active_config()
        assert active_config is not None
        assert active_config.name == "test-openai"

    def test_get_active_raises_when_none_activated(self):
        ProviderRegistry.clear()
        with pytest.raises(ProviderNotFoundError, match="当前没有激活的 provider"):
            ProviderRegistry.get_active()

    def test_activate_replaces_previous(self):
        config_a = ProviderConfig(
            name="provider-a",
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-a",
            api_host="https://api.a.com",
            model_id="model-a",
            display_name="A",
        )
        config_b = ProviderConfig(
            name="provider-b",
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-b",
            api_host="https://api.b.com",
            model_id="model-b",
            display_name="B",
        )
        ProviderRegistry.activate(config_a)
        ProviderRegistry.activate(config_b)

        active_config = ProviderRegistry.get_active_config()
        assert active_config.name == "provider-b"

    def test_clear_resets_active(self):
        config = ProviderConfig(
            name="test",
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-test",
            api_host="https://api.test.com",
            model_id="test-model",
            display_name="Test",
        )
        ProviderRegistry.activate(config)
        ProviderRegistry.clear()

        with pytest.raises(ProviderNotFoundError):
            ProviderRegistry.get_active()

    def test_unsupported_api_mode_raises(self):
        config = ProviderConfig.model_construct(
            name="bad",
            api_mode="unsupported-mode",
            api_key="sk-test",
            api_host="https://api.test.com",
            model_id="test-model",
            display_name="Bad",
        )
        with pytest.raises(ValueError, match="不支持的 API 模式"):
            ProviderRegistry.build_provider(config)

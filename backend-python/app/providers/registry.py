from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.providers.base import AIProvider
from app.providers.openai_compat_provider import OpenAICompatibleProvider


class ProviderNotFoundError(RuntimeError):
    pass


class ProviderRegistry:
    _active_provider: AIProvider | None = None
    _active_config: ProviderConfig | None = None

    @classmethod
    def build_provider(cls, config: ProviderConfig) -> AIProvider:
        if config.api_mode == ApiMode.OPENAI_COMPAT:
            return OpenAICompatibleProvider(config)
        raise ValueError(f"不支持的 API 模式: {config.api_mode}")

    @classmethod
    def activate(cls, config: ProviderConfig) -> AIProvider:
        provider = cls.build_provider(config)
        cls._active_provider = provider
        cls._active_config = config
        return provider

    @classmethod
    def get_active(cls) -> AIProvider:
        if cls._active_provider is None:
            raise ProviderNotFoundError("当前没有激活的 provider，请先配置并激活。")
        return cls._active_provider

    @classmethod
    def get_active_config(cls) -> ProviderConfig | None:
        return cls._active_config

    @classmethod
    def clear(cls) -> None:
        cls._active_provider = None
        cls._active_config = None

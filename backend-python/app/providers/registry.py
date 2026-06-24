from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.providers.base import AIProvider
from app.providers.openai_compat_provider import OpenAICompatibleProvider


class ProviderNotFoundError(RuntimeError):
    pass


class ProviderRegistry:
    _active_chat: AIProvider | None = None
    _active_embedding: AIProvider | None = None
    _active_chat_config: ProviderConfig | None = None
    _active_embedding_config: ProviderConfig | None = None

    @classmethod
    def build_provider(cls, config: ProviderConfig) -> AIProvider:
        if config.api_mode == ApiMode.OPENAI_COMPAT:
            return OpenAICompatibleProvider(config)
        raise ValueError(f"不支持的 API 模式: {config.api_mode}")

    @classmethod
    def activate(cls, config: ProviderConfig) -> AIProvider:
        provider = cls.build_provider(config)
        if config.purpose == Purpose.CHAT:
            cls._active_chat = provider
            cls._active_chat_config = config
        else:
            cls._active_embedding = provider
            cls._active_embedding_config = config
        return provider

    @classmethod
    def get_active_chat(cls) -> AIProvider:
        if cls._active_chat is None:
            raise ProviderNotFoundError("当前没有激活的 chat provider，请先配置并激活。")
        return cls._active_chat

    @classmethod
    def get_active_embedding(cls) -> AIProvider:
        if cls._active_embedding is None:
            raise ProviderNotFoundError("当前没有激活的 embedding provider，请先配置并激活。")
        return cls._active_embedding

    @classmethod
    def get_active_config(cls, purpose: Purpose) -> ProviderConfig | None:
        if purpose == Purpose.CHAT:
            return cls._active_chat_config
        return cls._active_embedding_config

    @classmethod
    def clear(cls, purpose: Purpose | None = None) -> None:
        if purpose is None:
            cls._active_chat = None
            cls._active_chat_config = None
            cls._active_embedding = None
            cls._active_embedding_config = None
        elif purpose == Purpose.CHAT:
            cls._active_chat = None
            cls._active_chat_config = None
        else:
            cls._active_embedding = None
            cls._active_embedding_config = None

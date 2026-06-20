"""当前激活的 Embedding Provider 注册表。"""

from app.providers.embedding_base import EmbeddingProvider


class EmbeddingProviderNotFoundError(RuntimeError):
    """当前没有可用的 Embedding Provider。"""


class EmbeddingProviderRegistry:
    """保存进程内当前激活的 Embedding Provider。"""

    _active_provider: EmbeddingProvider | None = None

    @classmethod
    def activate(cls, provider: EmbeddingProvider) -> EmbeddingProvider:
        cls._active_provider = provider
        return provider

    @classmethod
    def get_active(cls) -> EmbeddingProvider:
        if cls._active_provider is None:
            raise EmbeddingProviderNotFoundError(
                "当前没有激活的 Embedding Provider"
            )
        return cls._active_provider

    @classmethod
    def clear(cls) -> None:
        cls._active_provider = None

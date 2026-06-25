"""Embedding Provider 启动装配。"""

import logging
from dataclasses import dataclass
from pathlib import Path

from app.config.embedding_settings import (
    EmbeddingSettingsError,
    load_google_embedding_settings,
)
from app.providers.embedding_registry import EmbeddingProviderRegistry
from app.providers.google_embedding_provider import GoogleEmbeddingProvider

logger = logging.getLogger(__name__)

EMBEDDING_CONFIG_UNAVAILABLE_ERROR = "Embedding 配置不可用"


@dataclass(frozen=True)
class EmbeddingProviderSetupResult:
    """Embedding Provider 启动装配结果。"""

    available: bool
    error: str | None = None


def initialize_embedding_provider(
    secrets_path: str | Path | None = None,
) -> EmbeddingProviderSetupResult:
    """读取本地密钥配置并激活 Google Embedding Provider。"""

    try:
        settings = load_google_embedding_settings(secrets_path)
    except EmbeddingSettingsError:
        EmbeddingProviderRegistry.clear()
        logger.warning("Embedding Provider 未启用：配置不可用")
        return EmbeddingProviderSetupResult(
            available=False,
            error=EMBEDDING_CONFIG_UNAVAILABLE_ERROR,
        )

    provider = GoogleEmbeddingProvider(settings)
    EmbeddingProviderRegistry.activate(provider)
    return EmbeddingProviderSetupResult(available=True)


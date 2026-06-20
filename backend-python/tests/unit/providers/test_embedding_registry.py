from unittest.mock import MagicMock

import pytest

from app.providers.embedding_base import EmbeddingProvider
from app.providers.embedding_registry import (
    EmbeddingProviderNotFoundError,
    EmbeddingProviderRegistry,
)


def setup_function():
    EmbeddingProviderRegistry.clear()


def test_registry_activates_and_returns_provider():
    provider = MagicMock(spec=EmbeddingProvider)

    activated = EmbeddingProviderRegistry.activate(provider)

    assert activated is provider
    assert EmbeddingProviderRegistry.get_active() is provider


def test_registry_replaces_active_provider():
    first = MagicMock(spec=EmbeddingProvider)
    second = MagicMock(spec=EmbeddingProvider)

    EmbeddingProviderRegistry.activate(first)
    EmbeddingProviderRegistry.activate(second)

    assert EmbeddingProviderRegistry.get_active() is second


def test_registry_clear_removes_active_provider():
    EmbeddingProviderRegistry.activate(MagicMock(spec=EmbeddingProvider))

    EmbeddingProviderRegistry.clear()

    with pytest.raises(EmbeddingProviderNotFoundError):
        EmbeddingProviderRegistry.get_active()


def test_registry_raises_when_no_provider_is_active():
    with pytest.raises(
        EmbeddingProviderNotFoundError,
        match="没有激活的 Embedding Provider",
    ):
        EmbeddingProviderRegistry.get_active()

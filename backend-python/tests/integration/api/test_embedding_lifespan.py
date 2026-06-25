"""FastAPI lifespan 中 Embedding Provider 启动状态测试。"""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.providers.embedding_registry import (
    EmbeddingProviderNotFoundError,
    EmbeddingProviderRegistry,
)


@pytest.fixture(autouse=True)
def clear_embedding_registry():
    EmbeddingProviderRegistry.clear()
    yield
    EmbeddingProviderRegistry.clear()


def test_fastapi_startup_sets_embedding_available_and_shutdown_clears_provider(
    monkeypatch,
):
    fake_provider = SimpleNamespace(name="active-google-provider")

    def fake_initialize_embedding_provider():
        EmbeddingProviderRegistry.activate(fake_provider)
        return SimpleNamespace(available=True, error=None)

    monkeypatch.setattr(
        main_module,
        "initialize_embedding_provider",
        fake_initialize_embedding_provider,
        raising=False,
    )

    with TestClient(main_module.app):
        assert main_module.app.state.embedding_available is True
        assert main_module.app.state.embedding_error is None
        assert EmbeddingProviderRegistry.get_active() is fake_provider

    with pytest.raises(EmbeddingProviderNotFoundError):
        EmbeddingProviderRegistry.get_active()


def test_fastapi_startup_allows_embedding_unavailable(monkeypatch):
    def fake_initialize_embedding_provider():
        return SimpleNamespace(available=False, error="Embedding 配置不可用")

    monkeypatch.setattr(
        main_module,
        "initialize_embedding_provider",
        fake_initialize_embedding_provider,
        raising=False,
    )

    with TestClient(main_module.app):
        assert main_module.app.state.embedding_available is False
        assert main_module.app.state.embedding_error == "Embedding 配置不可用"


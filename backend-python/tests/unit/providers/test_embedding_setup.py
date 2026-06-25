"""Embedding Provider 启动装配测试。"""

from types import SimpleNamespace

import pytest

from app.config.embedding_settings import EmbeddingSettingsError, GoogleEmbeddingSettings
from app.providers.embedding_registry import (
    EmbeddingProviderNotFoundError,
    EmbeddingProviderRegistry,
)


def _load_setup_module():
    try:
        from app.providers import embedding_setup
    except ModuleNotFoundError as exc:
        if exc.name == "app.providers.embedding_setup":
            pytest.fail("缺少 app.providers.embedding_setup 启动装配模块")
        raise
    return embedding_setup


@pytest.fixture(autouse=True)
def clear_embedding_registry():
    EmbeddingProviderRegistry.clear()
    yield
    EmbeddingProviderRegistry.clear()


def test_initialize_embedding_provider_activates_google_provider_without_embedding_request(
    monkeypatch,
):
    """有效密钥配置应只装配 provider，不发起 embedding API 请求。"""
    embedding_setup = _load_setup_module()
    settings = GoogleEmbeddingSettings(api_key="test-key")
    fake_provider = SimpleNamespace(name="fake-google-provider")
    created_with = []

    def fake_load_settings(*_args, **_kwargs):
        return settings

    def fake_create_google_provider(provider_settings):
        created_with.append(provider_settings)
        return fake_provider

    monkeypatch.setattr(
        embedding_setup,
        "load_google_embedding_settings",
        fake_load_settings,
    )
    monkeypatch.setattr(
        embedding_setup,
        "GoogleEmbeddingProvider",
        fake_create_google_provider,
    )

    result = embedding_setup.initialize_embedding_provider()

    assert result.available is True
    assert result.error is None
    assert EmbeddingProviderRegistry.get_active() is fake_provider
    assert created_with == [settings]


def test_initialize_embedding_provider_marks_config_error_unavailable_without_leaking_secret(
    monkeypatch,
    caplog,
):
    """配置异常应允许后端继续启动，并且不得把密钥写入结果或日志。"""
    embedding_setup = _load_setup_module()
    leaked_api_key = "SECRET-API-KEY"

    EmbeddingProviderRegistry.activate(SimpleNamespace(name="stale-provider"))

    def fake_load_settings(*_args, **_kwargs):
        raise EmbeddingSettingsError(f"invalid key {leaked_api_key}")

    def fail_if_provider_created(_settings):
        raise AssertionError("配置无效时不应创建 GoogleEmbeddingProvider")

    monkeypatch.setattr(
        embedding_setup,
        "load_google_embedding_settings",
        fake_load_settings,
    )
    monkeypatch.setattr(
        embedding_setup,
        "GoogleEmbeddingProvider",
        fail_if_provider_created,
    )

    result = embedding_setup.initialize_embedding_provider()

    assert result.available is False
    assert result.error == "Embedding 配置不可用"
    assert leaked_api_key not in caplog.text
    assert leaked_api_key not in str(result)
    with pytest.raises(EmbeddingProviderNotFoundError):
        EmbeddingProviderRegistry.get_active()


def test_initialize_embedding_provider_does_not_swallow_unexpected_provider_errors(
    monkeypatch,
):
    """非配置类编程错误不应被静默吞掉。"""
    embedding_setup = _load_setup_module()

    monkeypatch.setattr(
        embedding_setup,
        "load_google_embedding_settings",
        lambda *_args, **_kwargs: GoogleEmbeddingSettings(api_key="test-key"),
    )

    def raise_programming_error(_settings):
        raise RuntimeError("provider constructor bug")

    monkeypatch.setattr(
        embedding_setup,
        "GoogleEmbeddingProvider",
        raise_programming_error,
    )

    with pytest.raises(RuntimeError, match="provider constructor bug"):
        embedding_setup.initialize_embedding_provider()

import json

import pytest

from app.config import embedding_settings
from app.config.embedding_settings import (
    EmbeddingSettingsError,
    load_google_embedding_settings,
)

SECRET_API_KEY = "google-secret-test-key"


def write_secrets(path, content: object) -> None:
    path.write_text(json.dumps(content), encoding="utf-8")


def test_load_google_embedding_settings_from_json(tmp_path):
    secrets_path = tmp_path / "embedding.json"
    write_secrets(secrets_path, {"google": {"api_key": SECRET_API_KEY}})

    settings = load_google_embedding_settings(secrets_path)

    assert settings.api_key.get_secret_value() == SECRET_API_KEY
    assert settings.model_id == "gemini-embedding-001"
    assert settings.output_dimension == 768
    assert SECRET_API_KEY not in repr(settings)


def test_load_google_embedding_settings_selects_active_provider_from_new_format(tmp_path):
    secrets_path = tmp_path / "embedding_providers.json"
    write_secrets(
        secrets_path,
        {
            "active": "google-default",
            "providers": {
                "google-default": {
                    "api_mode": "google",
                    "api_key": SECRET_API_KEY,
                    "model_id": "text-embedding-004",
                    "dimension": 768,
                },
                "openai-small": {
                    "api_mode": "openai-compat",
                    "api_key": "unused-key",
                    "api_host": "https://api.openai.com/v1",
                    "model_id": "text-embedding-3-small",
                    "dimension": 1536,
                },
            },
        },
    )

    settings = load_google_embedding_settings(secrets_path)

    assert settings.api_key.get_secret_value() == SECRET_API_KEY
    assert settings.model_id == "text-embedding-004"
    assert settings.output_dimension == 768


def test_load_google_embedding_settings_rejects_missing_active_provider(tmp_path):
    secrets_path = tmp_path / "embedding_providers.json"
    write_secrets(
        secrets_path,
        {
            "active": "missing",
            "providers": {
                "google-default": {
                    "api_mode": "google",
                    "api_key": SECRET_API_KEY,
                    "model_id": "text-embedding-004",
                    "dimension": 768,
                },
            },
        },
    )

    with pytest.raises(EmbeddingSettingsError, match="active 指向不存在"):
        load_google_embedding_settings(secrets_path)


def test_load_google_embedding_settings_rejects_unsupported_api_mode_without_key_leak(
    tmp_path,
):
    secrets_path = tmp_path / "embedding_providers.json"
    write_secrets(
        secrets_path,
        {
            "active": "openai-small",
            "providers": {
                "openai-small": {
                    "api_mode": "openai-compat",
                    "api_key": SECRET_API_KEY,
                    "api_host": "https://api.openai.com/v1",
                    "model_id": "text-embedding-3-small",
                    "dimension": 1536,
                },
            },
        },
    )

    with pytest.raises(EmbeddingSettingsError, match="不支持的 Embedding api_mode") as exc_info:
        load_google_embedding_settings(secrets_path)

    assert SECRET_API_KEY not in str(exc_info.value)


def test_load_google_embedding_settings_uses_default_path(tmp_path, monkeypatch):
    secrets_path = tmp_path / "embedding.json"
    write_secrets(secrets_path, {"google": {"api_key": SECRET_API_KEY}})
    monkeypatch.setattr(
        embedding_settings,
        "DEFAULT_EMBEDDING_SECRETS_PATH",
        secrets_path,
    )

    settings = load_google_embedding_settings()

    assert settings.api_key.get_secret_value() == SECRET_API_KEY


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ({}, "google.api_key"),
        ({"google": {}}, "google.api_key"),
        ({"google": {"api_key": "  "}}, "google.api_key"),
    ],
)
def test_load_google_embedding_settings_rejects_missing_or_blank_key(
    tmp_path, content, message
):
    secrets_path = tmp_path / "embedding.json"
    write_secrets(secrets_path, content)

    with pytest.raises(EmbeddingSettingsError, match=message) as exc_info:
        load_google_embedding_settings(secrets_path)

    assert SECRET_API_KEY not in str(exc_info.value)


def test_load_google_embedding_settings_rejects_missing_file(tmp_path):
    with pytest.raises(EmbeddingSettingsError, match="不存在"):
        load_google_embedding_settings(tmp_path / "missing.json")


def test_load_google_embedding_settings_rejects_invalid_json_without_leaking_content(
    tmp_path,
):
    secrets_path = tmp_path / "embedding.json"
    secrets_path.write_text(
        '{"google": {"api_key": "google-secret-test-key"',
        encoding="utf-8",
    )

    with pytest.raises(EmbeddingSettingsError, match="JSON") as exc_info:
        load_google_embedding_settings(secrets_path)

    assert SECRET_API_KEY not in str(exc_info.value)

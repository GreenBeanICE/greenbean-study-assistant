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

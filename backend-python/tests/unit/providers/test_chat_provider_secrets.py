import json
import sqlite3
from contextlib import closing

import pytest

from app.providers.base import ProviderConfigurationError
from app.providers.chat_provider_secrets import (
    chat_api_key_secret_ref,
    load_active_chat_provider_config,
    resolve_chat_api_key,
)

SECRET_API_KEY = "real-chat-secret-test-key"


def write_secrets(path, content: object) -> None:
    path.write_text(json.dumps(content), encoding="utf-8")


def chat_secrets_payload(
    *,
    active: str = "google-gemini-chat",
    api_mode: str = "openai-compat",
    api_key: str = SECRET_API_KEY,
) -> dict:
    return {
        "active": active,
        "providers": {
            "google-gemini-chat": {
                "api_mode": api_mode,
                "api_key": api_key,
                "api_host": "https://generativelanguage.googleapis.com/v1beta/openai",
                "api_path": "/v1/chat/completions",
                "model_id": "gemini-2.5-flash",
                "display_name": "Google Gemini Chat",
                "context_window": 65536,
                "max_output_tokens": 8192,
            },
            "openai-mini": {
                "api_mode": "openai-compat",
                "api_key": "unused-openai-key",
                "api_host": "https://api.openai.com/v1",
                "api_path": "/v1/chat/completions",
                "model_id": "gpt-4o-mini",
                "display_name": "OpenAI GPT-4o mini",
                "context_window": 128000,
                "max_output_tokens": 8192,
            },
        },
    }


def sqlite_url(database_path) -> str:
    return f"sqlite:///{database_path.as_posix()}"


def load_test_sqlite_vec(connection: sqlite3.Connection) -> None:
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def test_load_active_chat_provider_config_selects_active_and_stores_secret_ref(tmp_path):
    secrets_path = tmp_path / "chat_providers.json"
    write_secrets(secrets_path, chat_secrets_payload())

    config = load_active_chat_provider_config(secrets_path)

    assert config.name == "google-gemini-chat"
    assert config.api_mode.value == "openai-compat"
    assert config.model_id == "gemini-2.5-flash"
    assert config.api_key == chat_api_key_secret_ref("google-gemini-chat")
    assert SECRET_API_KEY not in repr(config)


def test_load_active_chat_provider_config_rejects_missing_active_provider(tmp_path):
    secrets_path = tmp_path / "chat_providers.json"
    write_secrets(secrets_path, chat_secrets_payload(active="missing-provider"))

    with pytest.raises(ProviderConfigurationError, match="active 指向不存在"):
        load_active_chat_provider_config(secrets_path)


def test_load_active_chat_provider_config_rejects_unsupported_api_mode_without_key_leak(
    tmp_path,
):
    secrets_path = tmp_path / "chat_providers.json"
    write_secrets(secrets_path, chat_secrets_payload(api_mode="native-google"))

    with pytest.raises(ProviderConfigurationError, match="不支持的 Chat provider api_mode") as exc_info:
        load_active_chat_provider_config(secrets_path)

    assert SECRET_API_KEY not in str(exc_info.value)


def test_resolve_chat_api_key_keeps_legacy_plain_value():
    assert resolve_chat_api_key("sk-legacy-test") == "sk-legacy-test"


def test_resolve_chat_api_key_reads_secret_ref(tmp_path):
    secrets_path = tmp_path / "chat_providers.json"
    write_secrets(secrets_path, chat_secrets_payload())

    value = resolve_chat_api_key(
        chat_api_key_secret_ref("google-gemini-chat"),
        secrets_path,
    )

    assert value == SECRET_API_KEY


def test_resolve_chat_api_key_failure_does_not_leak_secret(tmp_path):
    secrets_path = tmp_path / "chat_providers.json"
    write_secrets(secrets_path, chat_secrets_payload())

    with pytest.raises(ProviderConfigurationError) as exc_info:
        resolve_chat_api_key(
            chat_api_key_secret_ref("missing-provider"),
            secrets_path,
        )

    assert SECRET_API_KEY not in str(exc_info.value)


def test_configure_chat_provider_persists_secret_ref_idempotently(tmp_path, monkeypatch):
    from app.db.connection import reset_runtime_database_state
    from app.providers import chat_provider_secrets
    from app.providers.configure_chat_providers import configure_active_chat_provider
    from app.providers.registry import ProviderRegistry

    secrets_path = tmp_path / "chat_providers.json"
    database_path = tmp_path / "provider.sqlite3"
    write_secrets(secrets_path, chat_secrets_payload())
    monkeypatch.setattr(
        chat_provider_secrets,
        "DEFAULT_CHAT_PROVIDERS_SECRETS_PATH",
        secrets_path,
    )

    try:
        for _ in range(2):
            config = configure_active_chat_provider(
                secrets_path=secrets_path,
                database_url=sqlite_url(database_path),
                sqlite_vec_loader=load_test_sqlite_vec,
            )
            assert config.api_key == chat_api_key_secret_ref("google-gemini-chat")

        with closing(sqlite3.connect(database_path)) as connection:
            rows = connection.execute(
                """
                SELECT name, api_key, is_active
                FROM provider_configs
                WHERE name = ?
                """,
                ("google-gemini-chat",),
            ).fetchall()
    finally:
        ProviderRegistry.clear()
        reset_runtime_database_state()

    assert rows == [("google-gemini-chat", chat_api_key_secret_ref("google-gemini-chat"), 1)]
    assert SECRET_API_KEY not in str(rows)

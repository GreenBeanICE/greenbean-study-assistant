import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.providers.registry import ProviderRegistry


def _write_configs(path: Path, configs):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"providers": [c.model_dump(mode="json") for c in configs]}),
        encoding="utf-8",
    )


def test_lifespan_restores_active_providers(tmp_path, monkeypatch):
    config_path = tmp_path / "provider_configs.json"
    monkeypatch.setattr("app.config.settings.PROVIDER_CONFIGS_PATH", config_path)
    monkeypatch.setattr("app.main.PROVIDER_CONFIGS_PATH", config_path)

    from app.entities.provider_config import ProviderConfig

    chat = ProviderConfig(
        name="chat-1",
        api_mode=ApiMode.OPENAI_COMPAT,
        api_key="sk-chat",
        api_host="https://api.chat.com",
        model_id="chat-model",
        display_name="Chat",
        purpose=Purpose.CHAT,
        is_active=True,
    )
    embed = ProviderConfig(
        name="embed-1",
        api_mode=ApiMode.OPENAI_COMPAT,
        api_key="sk-embed",
        api_host="https://api.embed.com",
        model_id="embed-model",
        display_name="Embed",
        purpose=Purpose.EMBEDDING,
        embedding_dimension=768,
        is_active=True,
    )
    _write_configs(config_path, [chat, embed])

    ProviderRegistry.clear()
    from app.main import app

    with TestClient(app):
        assert ProviderRegistry.get_active_config(Purpose.CHAT).name == "chat-1"
        assert ProviderRegistry.get_active_config(Purpose.EMBEDDING).name == "embed-1"

    ProviderRegistry.clear()

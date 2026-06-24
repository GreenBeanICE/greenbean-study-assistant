import json

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_provider_service
from app.config.settings import PROVIDER_CONFIGS_PATH
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.main import app
from app.providers.registry import ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository
from app.services.provider_service import ProviderService


@pytest.fixture
def isolated_provider_path(tmp_path, monkeypatch):
    path = tmp_path / "provider_configs.json"
    monkeypatch.setattr("app.config.settings.PROVIDER_CONFIGS_PATH", path)
    monkeypatch.setattr("app.main.PROVIDER_CONFIGS_PATH", path)
    service = ProviderService(ProviderConfigRepository(path))
    app.dependency_overrides[get_provider_service] = lambda: service
    yield path
    app.dependency_overrides.clear()
    ProviderRegistry.clear()


def _create(client, **overrides):
    payload = {
        "name": "provider-a",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-a",
        "api_host": "https://api-a.test.com",
        "model_id": "model-a",
        "display_name": "Provider A",
        "purpose": Purpose.CHAT,
    }
    payload.update(overrides)
    response = client.post("/api/providers", json=payload)
    assert response.status_code == 200
    return response.json()["data"]


def test_create_activate_persist_and_isolate_by_purpose(isolated_provider_path):
    client = TestClient(app)

    first = _create(client, name="chat-a", display_name="Chat A")
    second = _create(client, name="chat-b", display_name="Chat B")
    embed = _create(
        client,
        name="embed-a",
        display_name="Embed A",
        purpose=Purpose.EMBEDDING,
        embedding_dimension=512,
        model_id="embed-model",
    )

    activate_resp = client.post(f"/api/providers/{second['id']}/activate")
    assert activate_resp.status_code == 200
    client.post(f"/api/providers/{embed['id']}/activate")

    active_chat = client.get("/api/providers/active?purpose=chat").json()["data"]
    active_embed = client.get("/api/providers/active?purpose=embedding").json()["data"]
    assert active_chat["name"] == "chat-b"
    assert active_embed["name"] == "embed-a"

    persisted = json.loads(isolated_provider_path.read_text(encoding="utf-8"))["providers"]
    chat_active = [c for c in persisted if c["purpose"] == "chat" and c["is_active"]]
    embed_active = [c for c in persisted if c["purpose"] == "embedding" and c["is_active"]]
    assert [c["id"] for c in chat_active] == [second["id"]]
    assert [c["id"] for c in embed_active] == [embed["id"]]

    list_resp = client.get("/api/providers?purpose=chat")
    assert all("api_key" not in c for c in list_resp.json()["data"])

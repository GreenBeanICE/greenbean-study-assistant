from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_provider_service
from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.main import app
from app.services.provider_service import ProviderService


@pytest.fixture
def mock_service():
    return MagicMock(spec=ProviderService)


@pytest.fixture
def client(mock_service):
    app.dependency_overrides[get_provider_service] = lambda: mock_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_config(**overrides):
    kwargs = {
        "id": "cfg-1",
        "name": "test-cfg",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-test",
        "api_host": "https://api.test.com",
        "model_id": "test-model",
        "display_name": "Test",
        "purpose": Purpose.CHAT,
    }
    kwargs.update(overrides)
    return ProviderConfig(**kwargs)


def test_list_providers(client, mock_service):
    mock_service.list_all.return_value = []
    response = client.get("/api/providers?purpose=chat")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["data"] == []
    mock_service.list_all.assert_called_once_with(Purpose.CHAT)


def test_create_provider(client, mock_service):
    mock_service.create.return_value = _make_config(name="new-cfg")
    response = client.post(
        "/api/providers",
        json={
            "name": "new-cfg",
            "api_mode": ApiMode.OPENAI_COMPAT,
            "api_key": "sk-key",
            "api_host": "https://api.test.com",
            "model_id": "test-model",
            "display_name": "New",
            "purpose": Purpose.CHAT,
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "new-cfg"
    assert "api_key" not in response.json()["data"]


def test_activate_provider(client, mock_service):
    mock_service.activate.return_value = _make_config(name="test-cfg", is_active=True)
    response = client.post("/api/providers/cfg-1/activate")
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "test-cfg"


def test_get_active_provider(client, mock_service):
    mock_service.get_active.return_value = _make_config(name="test-cfg", is_active=True)
    response = client.get("/api/providers/active?purpose=chat")
    assert response.status_code == 200
    mock_service.get_active.assert_called_once_with(Purpose.CHAT)


def test_get_active_provider_none_returns_404(client, mock_service):
    mock_service.get_active.return_value = None
    response = client.get("/api/providers/active?purpose=chat")
    assert response.status_code == 404


def test_delete_provider(client, mock_service):
    mock_service.delete.return_value = True
    response = client.delete("/api/providers/cfg-1")
    assert response.status_code == 200


def test_create_provider_rejects_invalid_purpose_dimension_combination(client, mock_service):
    mock_service.create.return_value = _make_config(name="new-cfg")

    response = client.post(
        "/api/providers",
        json={
            "name": "bad-chat",
            "api_mode": ApiMode.OPENAI_COMPAT,
            "api_key": "sk-key",
            "api_host": "https://api.test.com",
            "model_id": "test-model",
            "display_name": "Bad Chat",
            "purpose": Purpose.CHAT,
            "embedding_dimension": 128,
        },
    )

    assert response.status_code == 422
    mock_service.create.assert_not_called()

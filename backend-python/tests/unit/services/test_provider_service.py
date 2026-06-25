import pytest
from pydantic import ValidationError

from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.providers.registry import ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository
from app.services.provider_service import ProviderService


@pytest.fixture
def repo(tmp_path):
    return ProviderConfigRepository(tmp_path / "provider_configs.json")


@pytest.fixture(autouse=True)
def reset_registry():
    ProviderRegistry.clear()
    yield
    ProviderRegistry.clear()


def _chat_payload(**overrides):
    payload = {
        "name": "chat-1",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-chat",
        "api_host": "https://api.chat.com",
        "model_id": "chat-model",
        "display_name": "Chat",
        "purpose": Purpose.CHAT,
    }
    payload.update(overrides)
    return payload


def _embedding_payload(**overrides):
    payload = {
        "name": "embed-1",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-embed",
        "api_host": "https://api.embed.com",
        "model_id": "embed-model",
        "display_name": "Embed",
        "purpose": Purpose.EMBEDDING,
        "embedding_dimension": 1024,
    }
    payload.update(overrides)
    return payload


def test_create_persists_via_repository(repo):
    service = ProviderService(repo)
    result = service.create(_chat_payload())
    assert result.name == "chat-1"
    assert repo.get_by_id(result.id).name == "chat-1"


def test_list_all_and_by_purpose(repo):
    service = ProviderService(repo)
    service.create(_chat_payload())
    service.create(_embedding_payload())
    assert len(service.list_all()) == 2
    assert len(service.list_all(Purpose.CHAT)) == 1
    assert len(service.list_all(Purpose.EMBEDDING)) == 1


def test_activate_sets_active_and_registry(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    activated = service.activate(created.id)
    assert activated.is_active is True
    assert ProviderRegistry.get_active_config(Purpose.CHAT).id == created.id


def test_activate_deactivates_only_same_purpose(repo):
    service = ProviderService(repo)
    chat_a = service.create(_chat_payload(name="a"))
    chat_b = service.create(_chat_payload(name="b"))
    embed = service.create(_embedding_payload())
    service.activate(chat_a.id)
    service.activate(embed.id)
    service.activate(chat_b.id)
    assert repo.get_by_id(chat_a.id).is_active is False
    assert repo.get_by_id(chat_b.id).is_active is True
    assert repo.get_by_id(embed.id).is_active is True


def test_activate_nonexistent_returns_none(repo):
    assert ProviderService(repo).activate("missing") is None


def test_get_active_by_purpose(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    service.activate(created.id)
    assert service.get_active(Purpose.CHAT).id == created.id
    assert service.get_active(Purpose.EMBEDDING) is None


def test_update(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    updated = service.update(created.id, {"display_name": "New"})
    assert updated.display_name == "New"


def test_update_reactivates_when_currently_active(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    service.activate(created.id)
    service.update(created.id, {"display_name": "New"})
    assert ProviderRegistry.get_active_config(Purpose.CHAT).display_name == "New"


def test_delete(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    assert service.delete(created.id) is True
    assert service.delete(created.id) is False


def test_delete_active_clears_registry(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    service.activate(created.id)
    service.delete(created.id)
    assert ProviderRegistry.get_active_config(Purpose.CHAT) is None


def test_delete_inactive_keeps_registry(repo):
    service = ProviderService(repo)
    active = service.create(_chat_payload(name="a"))
    service.activate(active.id)
    other = service.create(_chat_payload(name="b"))
    service.delete(other.id)
    assert ProviderRegistry.get_active_config(Purpose.CHAT).id == active.id


def test_update_rejects_invalid_purpose_transition_and_keeps_persisted_config(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())

    with pytest.raises(ValidationError):
        service.update(created.id, {"purpose": Purpose.EMBEDDING})

    persisted = repo.get_by_id(created.id)
    assert persisted.purpose == Purpose.CHAT
    assert persisted.embedding_dimension is None


def test_update_moves_active_provider_between_registry_slots(repo):
    service = ProviderService(repo)
    created = service.create(_chat_payload())
    service.activate(created.id)

    updated = service.update(
        created.id,
        {"purpose": Purpose.EMBEDDING, "embedding_dimension": 512},
    )

    assert updated.purpose == Purpose.EMBEDDING
    assert updated.is_active is True
    assert repo.get_active_by_purpose(Purpose.CHAT) is None
    assert repo.get_active_by_purpose(Purpose.EMBEDDING).id == created.id
    assert ProviderRegistry.get_active_config(Purpose.CHAT) is None
    assert ProviderRegistry.get_active_config(Purpose.EMBEDDING).id == created.id

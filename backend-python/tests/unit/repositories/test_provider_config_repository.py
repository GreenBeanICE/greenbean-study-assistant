import json

import pytest

from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose
from app.repositories.provider_config_repository import ProviderConfigRepository


def _chat_config(**overrides):
    kwargs = {
        "name": "chat-1",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-chat",
        "api_host": "https://api.chat.com",
        "model_id": "chat-model",
        "display_name": "Chat",
        "purpose": Purpose.CHAT,
    }
    kwargs.update(overrides)
    return ProviderConfig(**kwargs)


def _embedding_config(**overrides):
    kwargs = {
        "name": "embed-1",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-embed",
        "api_host": "https://api.embed.com",
        "model_id": "embed-model",
        "display_name": "Embed",
        "purpose": Purpose.EMBEDDING,
        "embedding_dimension": 1024,
    }
    kwargs.update(overrides)
    return ProviderConfig(**kwargs)


def test_save_and_list_all(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    repo.save(_chat_config())
    repo.save(_embedding_config())
    assert len(repo.list_all()) == 2


def test_list_by_purpose(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    repo.save(_chat_config())
    repo.save(_embedding_config())
    assert len(repo.list_by_purpose(Purpose.CHAT)) == 1
    assert len(repo.list_by_purpose(Purpose.EMBEDDING)) == 1


def test_get_by_id(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    config = _chat_config()
    repo.save(config)
    assert repo.get_by_id(config.id).name == "chat-1"
    assert repo.get_by_id("missing") is None


def test_save_replaces_existing(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    config = _chat_config()
    repo.save(config)
    repo.save(config.model_copy(update={"display_name": "Updated"}))
    assert len(repo.list_all()) == 1
    assert repo.get_by_id(config.id).display_name == "Updated"


def test_delete(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    config = _chat_config()
    repo.save(config)
    assert repo.delete(config.id) is True
    assert repo.delete(config.id) is False
    assert repo.list_all() == []


def test_deactivate_by_purpose_only_affects_same_purpose(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    chat = _chat_config(is_active=True)
    embed = _embedding_config(is_active=True)
    repo.save(chat)
    repo.save(embed)
    repo.deactivate_by_purpose(Purpose.CHAT)
    assert repo.get_by_id(chat.id).is_active is False
    assert repo.get_by_id(embed.id).is_active is True


def test_get_active_by_purpose(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    repo.save(_chat_config(is_active=False))
    assert repo.get_active_by_purpose(Purpose.CHAT) is None
    active = _chat_config(name="chat-2", is_active=True)
    repo.save(active)
    assert repo.get_active_by_purpose(Purpose.CHAT).id == active.id


def test_empty_file_when_missing(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    assert repo.list_all() == []
    repo.save(_chat_config())
    payload = json.loads((tmp_path / "provider_configs.json").read_text(encoding="utf-8"))
    assert "providers" in payload
    assert len(payload["providers"]) == 1


def test_corrupted_file_raises(tmp_path):
    path = tmp_path / "provider_configs.json"
    path.write_text("{not valid json", encoding="utf-8")
    repo = ProviderConfigRepository(path)
    with pytest.raises(Exception):
        repo.list_all()


def test_atomic_write_no_tmp_left(tmp_path):
    repo = ProviderConfigRepository(tmp_path / "provider_configs.json")
    repo.save(_chat_config())
    assert list(tmp_path.glob("*.tmp")) == []

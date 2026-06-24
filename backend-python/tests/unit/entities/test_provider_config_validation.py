import pytest
from pydantic import ValidationError

from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose


def _base_kwargs(**overrides):
    kwargs = {
        "name": "cfg",
        "api_mode": ApiMode.OPENAI_COMPAT,
        "api_key": "sk-test",
        "api_host": "https://api.test.com",
        "model_id": "model",
        "display_name": "Cfg",
    }
    kwargs.update(overrides)
    return kwargs


def test_chat_config_rejects_embedding_dimension():
    with pytest.raises(ValidationError, match="chat 配置不能设置 embedding_dimension"):
        ProviderConfig(**_base_kwargs(purpose=Purpose.CHAT, embedding_dimension=1024))


def test_embedding_config_requires_positive_dimension():
    with pytest.raises(ValidationError, match="embedding 配置必须提供正整数 embedding_dimension"):
        ProviderConfig(**_base_kwargs(purpose=Purpose.EMBEDDING, embedding_dimension=None))


def test_embedding_config_rejects_non_positive_dimension():
    with pytest.raises(ValidationError, match="embedding 配置必须提供正整数 embedding_dimension"):
        ProviderConfig(**_base_kwargs(purpose=Purpose.EMBEDDING, embedding_dimension=0))


def test_embedding_config_accepts_dimension():
    config = ProviderConfig(**_base_kwargs(purpose=Purpose.EMBEDDING, embedding_dimension=1024))
    assert config.purpose == Purpose.EMBEDDING
    assert config.embedding_dimension == 1024


def test_chat_config_defaults_dimension_none():
    config = ProviderConfig(**_base_kwargs(purpose=Purpose.CHAT))
    assert config.embedding_dimension is None

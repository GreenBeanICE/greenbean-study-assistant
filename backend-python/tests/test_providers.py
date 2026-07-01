from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.provider_controller import ProviderController
from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.providers.base import ChatResult, ProviderConfigurationError
from app.providers.chat_provider_secrets import chat_api_key_secret_ref
from app.providers.openai_compat_provider import OpenAICompatibleProvider
from app.providers.registry import ProviderNotFoundError, ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository
from app.schemas.provider_schema import (
    ProviderActivateResponse,
    ProviderConfigCreateRequest,
    ProviderConfigUpdateRequest,
)
from app.services.provider_service import ProviderService


def make_config(name: str = "test-cfg", is_active: bool = False) -> ProviderConfig:
    return ProviderConfig(
        name=name, api_mode=ApiMode.OPENAI_COMPAT, api_key="sk-test",
        api_host="https://api.test.com", model_id="test-model",
        display_name=name, is_active=is_active,
    )


# ── Registry ─────────────────────────────────────────────────────────

class TestProviderRegistry:
    def setup_method(self):
        ProviderRegistry.clear()

    def test_build_openai_compat_provider(self):
        config = make_config(name="test-deepseek")
        provider = ProviderRegistry.build_provider(config)
        assert isinstance(provider, OpenAICompatibleProvider)

    def test_activate_and_get_active(self):
        config = make_config(name="test-openai", is_active=True)
        provider = ProviderRegistry.activate(config)
        assert ProviderRegistry.get_active() is provider
        assert ProviderRegistry.get_active_config().name == "test-openai"

    def test_get_active_raises_when_none_activated(self):
        ProviderRegistry.clear()
        with pytest.raises(ProviderNotFoundError, match="当前没有激活的 provider"):
            ProviderRegistry.get_active()

    def test_activate_replaces_previous(self):
        ProviderRegistry.activate(make_config(name="a"))
        ProviderRegistry.activate(make_config(name="b"))
        assert ProviderRegistry.get_active_config().name == "b"

    def test_clear_resets_active(self):
        ProviderRegistry.activate(make_config(name="t"))
        ProviderRegistry.clear()
        with pytest.raises(ProviderNotFoundError):
            ProviderRegistry.get_active()

    def test_unsupported_api_mode_raises(self):
        config = ProviderConfig.model_construct(
            name="bad", api_mode="unsupported-mode", api_key="sk-test",
            api_host="https://test.com", model_id="test", display_name="Bad",
        )
        with pytest.raises(ValueError, match="不支持的 API 模式"):
            ProviderRegistry.build_provider(config)


# ── Provider Implementation ──────────────────────────────────────────

class TestOpenAICompatibleProvider:
    def test_initializes_with_config(self):
        provider = OpenAICompatibleProvider(make_config())
        assert provider.config.name == "test-cfg"

    @patch("app.providers.openai_compat_provider.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_chat_completion_returns_content(self, MockAsyncOpenAI):
        mock_client = MockAsyncOpenAI.return_value
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="Hello"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = OpenAICompatibleProvider(make_config())
        result = await provider.chat_completion(messages=[{"role": "user", "content": "hi"}])
        assert isinstance(result, ChatResult)
        assert result.content == "Hello"

    @patch("app.providers.openai_compat_provider.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_chat_completion_passes_model_and_params(self, MockAsyncOpenAI):
        mock_client = MockAsyncOpenAI.return_value
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="OK"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = OpenAICompatibleProvider(make_config())
        await provider.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            model="override-model", temperature=0.5, max_tokens=100,
            response_format={"type": "json_object"},
        )
        kwargs = mock_client.chat.completions.create.call_args[1]
        assert kwargs["model"] == "override-model"
        assert kwargs["temperature"] == 0.5
        assert kwargs["max_tokens"] == 100
        assert kwargs["response_format"] == {"type": "json_object"}

    @patch("app.providers.openai_compat_provider.AsyncOpenAI")
    def test_initializes_with_secret_ref(self, MockAsyncOpenAI, tmp_path, monkeypatch):
        import json
        from app.providers import chat_provider_secrets

        secrets_path = tmp_path / "chat_providers.json"
        secrets_path.write_text(
            json.dumps(
                {
                    "active": "secret-provider",
                    "providers": {
                        "secret-provider": {
                            "api_mode": "openai-compat",
                            "api_key": "real-secret-key",
                            "api_host": "https://api.test.com/v1",
                            "model_id": "test-model",
                            "display_name": "Secret Provider",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            chat_provider_secrets,
            "DEFAULT_CHAT_PROVIDERS_SECRETS_PATH",
            secrets_path,
        )

        OpenAICompatibleProvider(
            ProviderConfig(
                name="secret-provider",
                api_mode=ApiMode.OPENAI_COMPAT,
                api_key=chat_api_key_secret_ref("secret-provider"),
                api_host="https://api.test.com/v1",
                model_id="test-model",
                display_name="Secret Provider",
            )
        )

        assert MockAsyncOpenAI.call_args.kwargs["api_key"] == "real-secret-key"

    def test_secret_ref_parse_failure_does_not_leak_key(self, tmp_path, monkeypatch):
        import json
        from app.providers import chat_provider_secrets

        secrets_path = tmp_path / "chat_providers.json"
        secrets_path.write_text(
            json.dumps(
                {
                    "active": "secret-provider",
                    "providers": {
                        "secret-provider": {
                            "api_mode": "openai-compat",
                            "api_key": "real-secret-key",
                            "api_host": "https://api.test.com/v1",
                            "model_id": "test-model",
                            "display_name": "Secret Provider",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            chat_provider_secrets,
            "DEFAULT_CHAT_PROVIDERS_SECRETS_PATH",
            secrets_path,
        )

        with pytest.raises(ProviderConfigurationError) as exc_info:
            OpenAICompatibleProvider(
                ProviderConfig(
                    name="missing-provider",
                    api_mode=ApiMode.OPENAI_COMPAT,
                    api_key=chat_api_key_secret_ref("missing-provider"),
                    api_host="https://api.test.com/v1",
                    model_id="test-model",
                    display_name="Missing Provider",
                )
            )

        assert "real-secret-key" not in str(exc_info.value)


# ── Service ──────────────────────────────────────────────────────────

class TestProviderService:
    @pytest.fixture
    def mock_uow(self):
        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.__exit__.return_value = None
        uow.session = MagicMock()
        return uow

    def test_create(self, mock_uow):
        service = ProviderService(uow=mock_uow)
        result = service.create(dict(
            name="new-cfg", api_mode=ApiMode.OPENAI_COMPAT, api_key="sk-new",
            api_host="https://api.new.com", model_id="new-model", display_name="New",
        ))
        assert result.name == "new-cfg"
        mock_uow.commit.assert_called_once()

    def test_get_by_id(self, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=make_config()):
            assert ProviderService(uow=mock_uow).get_by_id("some-id").name == "test-cfg"

    def test_get_by_id_returns_none(self, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=None):
            assert ProviderService(uow=mock_uow).get_by_id("missing") is None

    def test_list_all(self, mock_uow):
        with patch.object(ProviderConfigRepository, "list_all", return_value=[make_config()]):
            assert len(ProviderService(uow=mock_uow).list_all()) == 1

    def test_delete(self, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=make_config()):
            with patch.object(ProviderConfigRepository, "delete", return_value=True):
                assert ProviderService(uow=mock_uow).delete("some-id") is True

    def test_delete_nonexistent(self, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=None):
            assert ProviderService(uow=mock_uow).delete("missing") is False

    @patch("app.services.provider_service.ProviderRegistry")
    def test_activate(self, MockRegistry, mock_uow):
        config = make_config(name="to-activate")
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=config):
            with patch.object(ProviderConfigRepository, "save"):
                with patch.object(ProviderConfigRepository, "deactivate_all"):
                    result = ProviderService(uow=mock_uow).activate("some-id")
                    assert result.is_active is True
                    MockRegistry.activate.assert_called_once_with(config)

    @patch("app.services.provider_service.ProviderRegistry")
    def test_activate_nonexistent(self, MockRegistry, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=None):
            assert ProviderService(uow=mock_uow).activate("missing") is None
            MockRegistry.activate.assert_not_called()

    def test_update(self, mock_uow):
        config = make_config(name="original")
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=config):
            with patch.object(ProviderConfigRepository, "save"):
                with patch.object(ProviderConfigRepository, "list_all", return_value=[]):
                    result = ProviderService(uow=mock_uow).update(config.id, {"name": "updated"})
                    assert result.name == "updated"
                    mock_uow.commit.assert_called_once()

    def test_update_nonexistent(self, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=None):
            assert ProviderService(uow=mock_uow).update("missing", {"name": "nope"}) is None

    @patch("app.services.provider_service.ProviderRegistry")
    def test_update_reactivates_when_active(self, MockRegistry, mock_uow):
        config = make_config(name="active-cfg", is_active=True)
        MockRegistry.get_active_config.return_value = config
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=config):
            with patch.object(ProviderConfigRepository, "save"):
                result = ProviderService(uow=mock_uow).update(config.id, {"display_name": "Updated"})
                assert result.display_name == "Updated"
                MockRegistry.activate.assert_called_once_with(config)

    def test_get_active(self, mock_uow):
        config = make_config(is_active=True)
        with patch.object(ProviderConfigRepository, "get_active", return_value=config):
            assert ProviderService(uow=mock_uow).get_active().is_active is True

    def test_get_active_returns_none(self, mock_uow):
        with patch.object(ProviderConfigRepository, "get_active", return_value=None):
            assert ProviderService(uow=mock_uow).get_active() is None

    @patch("app.services.provider_service.ProviderRegistry")
    def test_delete_active_clears_registry(self, MockRegistry, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=make_config(is_active=True)):
            with patch.object(ProviderConfigRepository, "delete", return_value=True):
                assert ProviderService(uow=mock_uow).delete("active-id") is True
                MockRegistry.clear.assert_called_once()

    def test_delete_inactive_does_not_clear_registry(self, mock_uow):
        with patch.object(ProviderConfigRepository, "get_by_id", return_value=make_config(is_active=False)):
            with patch.object(ProviderConfigRepository, "delete", return_value=True):
                assert ProviderService(uow=mock_uow).delete("inactive-id") is True


# ── Controller ───────────────────────────────────────────────────────

class TestProviderController:
    @pytest.fixture
    def mock_service(self):
        return MagicMock(spec=ProviderService)

    @pytest.fixture
    def controller(self, mock_service):
        return ProviderController(mock_service)

    @pytest.mark.asyncio
    async def test_list_providers(self, controller, mock_service):
        mock_service.list_all.return_value = [make_config()]
        result = await controller.list_providers()
        assert len(result) == 1
        assert result[0].name == "test-cfg"

    @pytest.mark.asyncio
    async def test_get_provider(self, controller, mock_service):
        mock_service.get_by_id.return_value = make_config()
        result = await controller.get_provider("some-id")
        assert result.name == "test-cfg"

    @pytest.mark.asyncio
    async def test_get_provider_returns_none(self, controller, mock_service):
        mock_service.get_by_id.return_value = None
        assert await controller.get_provider("missing") is None

    @pytest.mark.asyncio
    async def test_create_provider(self, controller, mock_service):
        cfg = make_config(name="new-cfg")
        mock_service.create.return_value = cfg
        req = ProviderConfigCreateRequest(
            name="new-cfg", api_mode=ApiMode.OPENAI_COMPAT, api_key="sk-key",
            api_host="https://api.test.com", model_id="test-model", display_name="New",
        )
        result = await controller.create_provider(req)
        assert result.name == "new-cfg"

    @pytest.mark.asyncio
    async def test_update_provider(self, controller, mock_service):
        cfg = make_config(name="updated")
        mock_service.update.return_value = cfg
        req = ProviderConfigUpdateRequest(display_name="Updated")
        result = await controller.update_provider("some-id", req)
        assert result.name == "updated"

    @pytest.mark.asyncio
    async def test_update_provider_returns_none(self, controller, mock_service):
        mock_service.update.return_value = None
        req = ProviderConfigUpdateRequest(display_name="Nope")
        assert await controller.update_provider("missing", req) is None

    @pytest.mark.asyncio
    async def test_delete_provider(self, controller, mock_service):
        mock_service.delete.return_value = True
        assert await controller.delete_provider("some-id") is True

    @pytest.mark.asyncio
    async def test_delete_provider_false(self, controller, mock_service):
        mock_service.delete.return_value = False
        assert await controller.delete_provider("missing") is False

    @pytest.mark.asyncio
    async def test_activate_provider(self, controller, mock_service):
        cfg = make_config(name="activate-me", is_active=True)
        mock_service.activate.return_value = cfg
        result = await controller.activate_provider("some-id")
        assert isinstance(result, ProviderActivateResponse)
        assert result.name == "activate-me"

    @pytest.mark.asyncio
    async def test_activate_provider_returns_none(self, controller, mock_service):
        mock_service.activate.return_value = None
        assert await controller.activate_provider("missing") is None

    @pytest.mark.asyncio
    async def test_get_active_provider(self, controller, mock_service):
        cfg = make_config(name="active-cfg", is_active=True)
        mock_service.get_active.return_value = cfg
        result = await controller.get_active_provider()
        assert isinstance(result, ProviderActivateResponse)
        assert result.name == "active-cfg"

    @pytest.mark.asyncio
    async def test_get_active_provider_returns_none(self, controller, mock_service):
        mock_service.get_active.return_value = None
        assert await controller.get_active_provider() is None


# ── todo_prompts.py ──────────────────────────────────────────────────

def test_todo_prompts_import_and_template():
    from app.prompts.todo_prompts import TODO_SYSTEM_PROMPT, TODO_USER_PROMPT_TPL
    assert "study-plan" in TODO_SYSTEM_PROMPT
    result = TODO_USER_PROMPT_TPL.substitute(
        document_title="Doc", analysis_summary="Sum",
        key_concepts="A,B", highlights="H",
    )
    assert "Doc" in result
    assert "A,B" in result

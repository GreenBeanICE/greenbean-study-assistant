from unittest.mock import MagicMock

import pytest

from app.api.provider_controller import ProviderController
from app.enums.api_mode import ApiMode
from app.schemas.provider_schema import (
    ProviderActivateResponse,
    ProviderConfigCreateRequest,
    ProviderConfigUpdateRequest,
)
from app.services.provider_service import ProviderService


class TestProviderController:
    @pytest.fixture
    def mock_service(self):
        return MagicMock(spec=ProviderService)

    @pytest.fixture
    def controller(self, mock_service):
        return ProviderController(mock_service)

    @pytest.mark.asyncio
    async def test_list_providers(
        self, controller, mock_service, provider_config_factory
    ):
        mock_service.list_all.return_value = [provider_config_factory()]
        result = await controller.list_providers()
        assert len(result) == 1
        assert result[0].name == "test-cfg"

    @pytest.mark.asyncio
    async def test_get_provider(
        self, controller, mock_service, provider_config_factory
    ):
        mock_service.get_by_id.return_value = provider_config_factory()
        result = await controller.get_provider("some-id")
        assert result.name == "test-cfg"

    @pytest.mark.asyncio
    async def test_get_provider_returns_none(self, controller, mock_service):
        mock_service.get_by_id.return_value = None
        assert await controller.get_provider("missing") is None

    @pytest.mark.asyncio
    async def test_create_provider(
        self, controller, mock_service, provider_config_factory
    ):
        config = provider_config_factory(name="new-cfg")
        mock_service.create.return_value = config
        request = ProviderConfigCreateRequest(
            name="new-cfg",
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-key",
            api_host="https://api.test.com",
            model_id="test-model",
            display_name="New",
        )
        result = await controller.create_provider(request)
        assert result.name == "new-cfg"

    @pytest.mark.asyncio
    async def test_update_provider(
        self, controller, mock_service, provider_config_factory
    ):
        config = provider_config_factory(name="updated")
        mock_service.update.return_value = config
        request = ProviderConfigUpdateRequest(display_name="Updated")
        result = await controller.update_provider("some-id", request)
        assert result.name == "updated"

    @pytest.mark.asyncio
    async def test_update_provider_returns_none(self, controller, mock_service):
        mock_service.update.return_value = None
        request = ProviderConfigUpdateRequest(display_name="Nope")
        assert await controller.update_provider("missing", request) is None

    @pytest.mark.asyncio
    async def test_delete_provider(self, controller, mock_service):
        mock_service.delete.return_value = True
        assert await controller.delete_provider("some-id") is True

    @pytest.mark.asyncio
    async def test_delete_provider_false(self, controller, mock_service):
        mock_service.delete.return_value = False
        assert await controller.delete_provider("missing") is False

    @pytest.mark.asyncio
    async def test_activate_provider(
        self, controller, mock_service, provider_config_factory
    ):
        config = provider_config_factory(name="activate-me", is_active=True)
        mock_service.activate.return_value = config
        result = await controller.activate_provider("some-id")
        assert isinstance(result, ProviderActivateResponse)
        assert result.name == "activate-me"

    @pytest.mark.asyncio
    async def test_activate_provider_returns_none(self, controller, mock_service):
        mock_service.activate.return_value = None
        assert await controller.activate_provider("missing") is None

    @pytest.mark.asyncio
    async def test_get_active_provider(
        self, controller, mock_service, provider_config_factory
    ):
        config = provider_config_factory(name="active-cfg", is_active=True)
        mock_service.get_active.return_value = config
        result = await controller.get_active_provider()
        assert isinstance(result, ProviderActivateResponse)
        assert result.name == "active-cfg"

    @pytest.mark.asyncio
    async def test_get_active_provider_returns_none(self, controller, mock_service):
        mock_service.get_active.return_value = None
        assert await controller.get_active_provider() is None

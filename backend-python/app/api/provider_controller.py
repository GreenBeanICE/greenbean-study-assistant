from app.schemas.provider_schema import (
    ProviderActivateResponse,
    ProviderConfigCreateRequest,
    ProviderConfigResponse,
    ProviderConfigUpdateRequest,
)
from app.services.provider_service import ProviderService


class ProviderController:
    def __init__(self, service: ProviderService) -> None:
        self.service = service

    async def list_providers(self) -> list[ProviderConfigResponse]:
        configs = self.service.list_all()
        return [self._to_response(c) for c in configs]

    async def get_provider(self, config_id: str) -> ProviderConfigResponse | None:
        config = self.service.get_by_id(config_id)
        if config is None:
            return None
        return self._to_response(config)

    async def create_provider(self, request: ProviderConfigCreateRequest) -> ProviderConfigResponse:
        config = self.service.create(request.model_dump())
        return self._to_response(config)

    async def update_provider(
        self, config_id: str, request: ProviderConfigUpdateRequest
    ) -> ProviderConfigResponse | None:
        config = self.service.update(config_id, request.model_dump(exclude_none=True))
        if config is None:
            return None
        return self._to_response(config)

    async def delete_provider(self, config_id: str) -> bool:
        return self.service.delete(config_id)

    async def activate_provider(self, config_id: str) -> ProviderActivateResponse | None:
        config = self.service.activate(config_id)
        if config is None:
            return None
        return ProviderActivateResponse(
            id=config.id,
            name=config.name,
            display_name=config.display_name,
            model_id=config.model_id,
        )

    async def get_active_provider(self) -> ProviderActivateResponse | None:
        config = self.service.get_active()
        if config is None:
            return None
        return ProviderActivateResponse(
            id=config.id,
            name=config.name,
            display_name=config.display_name,
            model_id=config.model_id,
        )

    def _to_response(self, config) -> ProviderConfigResponse:
        return ProviderConfigResponse(
            id=config.id,
            name=config.name,
            api_mode=config.api_mode,
            api_host=config.api_host,
            api_path=config.api_path,
            model_id=config.model_id,
            display_name=config.display_name,
            context_window=config.context_window,
            max_output_tokens=config.max_output_tokens,
            purpose=config.purpose,
            embedding_dimension=config.embedding_dimension,
            is_active=config.is_active,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
        )

from app.entities.provider_config import ProviderConfig
from app.enums.purpose import Purpose
from app.providers.registry import ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository


class ProviderService:
    def __init__(self, repository: ProviderConfigRepository) -> None:
        self.repository = repository

    def create(self, data: dict) -> ProviderConfig:
        config = ProviderConfig(**data)
        self.repository.save(config)
        return config

    def update(self, config_id: str, data: dict) -> ProviderConfig | None:
        config = self.repository.get_by_id(config_id)
        if config is None:
            return None
        updated = config.model_copy(
            update={k: v for k, v in data.items() if v is not None}
        )
        self.repository.save(updated)
        active_config = ProviderRegistry.get_active_config(updated.purpose)
        if active_config is not None and active_config.id == config_id:
            ProviderRegistry.activate(updated)
        return updated

    def activate(self, config_id: str) -> ProviderConfig | None:
        config = self.repository.get_by_id(config_id)
        if config is None:
            return None
        self.repository.deactivate_by_purpose(config.purpose)
        activated = config.model_copy(update={"is_active": True})
        self.repository.save(activated)
        ProviderRegistry.activate(activated)
        return activated

    def get_active(self, purpose: Purpose) -> ProviderConfig | None:
        return self.repository.get_active_by_purpose(purpose)

    def get_by_id(self, config_id: str) -> ProviderConfig | None:
        return self.repository.get_by_id(config_id)

    def list_all(self, purpose: Purpose | None = None) -> list[ProviderConfig]:
        if purpose is not None:
            return self.repository.list_by_purpose(purpose)
        return self.repository.list_all()

    def delete(self, config_id: str) -> bool:
        config = self.repository.get_by_id(config_id)
        if config is None:
            return False
        deleted = self.repository.delete(config_id)
        if deleted and config.is_active:
            ProviderRegistry.clear(config.purpose)
        return deleted

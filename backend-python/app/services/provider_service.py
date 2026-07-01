from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.db.orm import SessionFactory
from app.entities.provider_config import ProviderConfig
from app.providers.registry import ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository


def activate_persisted_provider(
    session_factory: SessionFactory,
) -> ProviderConfig | None:
    """从 provider_configs 读取 active provider 并激活进程内 Registry。"""

    with session_factory() as session:
        config = ProviderConfigRepository(session).get_active()
    if config is None:
        ProviderRegistry.clear()
        return None
    ProviderRegistry.activate(config)
    return config


class ProviderService:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow

    def create(self, data: dict) -> ProviderConfig:
        with self.uow as uow:
            repo = ProviderConfigRepository(uow.session)
            config = ProviderConfig(**data)
            repo.save(config)
            uow.commit()
        return config

    def update(self, config_id: str, data: dict) -> ProviderConfig | None:
        with self.uow as uow:
            repo = ProviderConfigRepository(uow.session)
            config = repo.get_by_id(config_id)
            if config is None:
                return None
            for key, value in data.items():
                if value is not None:
                    setattr(config, key, value)
            repo.save(config)
            uow.commit()

            if ProviderRegistry.get_active_config() and ProviderRegistry.get_active_config().id == config_id:
                ProviderRegistry.activate(config)
        return config

    def activate(self, config_id: str) -> ProviderConfig | None:
        with self.uow as uow:
            repo = ProviderConfigRepository(uow.session)
            config = repo.get_by_id(config_id)
            if config is None:
                return None
            repo.deactivate_all()
            config.is_active = True
            repo.save(config)
            uow.commit()

        ProviderRegistry.activate(config)
        return config

    def get_active(self) -> ProviderConfig | None:
        with self.uow as uow:
            repo = ProviderConfigRepository(uow.session)
            return repo.get_active()

    def get_by_id(self, config_id: str) -> ProviderConfig | None:
        with self.uow as uow:
            repo = ProviderConfigRepository(uow.session)
            return repo.get_by_id(config_id)

    def list_all(self) -> list[ProviderConfig]:
        with self.uow as uow:
            repo = ProviderConfigRepository(uow.session)
            return repo.list_all()

    def delete(self, config_id: str) -> bool:
        with self.uow as uow:
            repo = ProviderConfigRepository(uow.session)
            config = repo.get_by_id(config_id)
            if config is None:
                return False
            was_active = config.is_active
            result = repo.delete(config_id)
            uow.commit()

            if was_active:
                ProviderRegistry.clear()
        return result

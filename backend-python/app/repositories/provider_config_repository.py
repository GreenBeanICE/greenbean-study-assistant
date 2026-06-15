from sqlalchemy.orm import Session

from app.db.models import ProviderConfigModel
from app.entities.provider_config import ProviderConfig
from app.repositories.sqlite_helpers import datetime_value


class ProviderConfigRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, config: ProviderConfig) -> ProviderConfig:
        model = self.session.get(ProviderConfigModel, config.id)
        if model is None:
            model = ProviderConfigModel(
                id=config.id,
                created_at=datetime_value(config.created_at),
            )
            self.session.add(model)
        model.name = config.name
        model.api_mode = config.api_mode.value
        model.api_key = config.api_key
        model.api_host = config.api_host
        model.api_path = config.api_path
        model.model_id = config.model_id
        model.display_name = config.display_name
        model.context_window = config.context_window
        model.max_output_tokens = config.max_output_tokens
        model.is_active = 1 if config.is_active else 0
        model.updated_at = datetime_value(config.updated_at)
        return config

    def get_by_id(self, config_id: str) -> ProviderConfig | None:
        model = self.session.get(ProviderConfigModel, config_id)
        if model is None:
            return None
        return self._to_entity(model)

    def get_by_name(self, name: str) -> ProviderConfig | None:
        model = self.session.query(ProviderConfigModel).filter(
            ProviderConfigModel.name == name
        ).first()
        if model is None:
            return None
        return self._to_entity(model)

    def get_active(self) -> ProviderConfig | None:
        model = self.session.query(ProviderConfigModel).filter(
            ProviderConfigModel.is_active == 1
        ).first()
        if model is None:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[ProviderConfig]:
        models = self.session.query(ProviderConfigModel).order_by(
            ProviderConfigModel.display_name
        ).all()
        return [self._to_entity(m) for m in models]

    def deactivate_all(self) -> None:
        self.session.query(ProviderConfigModel).filter(
            ProviderConfigModel.is_active == 1
        ).update({"is_active": 0})

    def delete(self, config_id: str) -> bool:
        model = self.session.get(ProviderConfigModel, config_id)
        if model is None:
            return False
        self.session.delete(model)
        return True

    def _to_entity(self, model: ProviderConfigModel) -> ProviderConfig:
        from app.enums.api_mode import ApiMode
        return ProviderConfig(
            id=model.id,
            name=model.name,
            api_mode=ApiMode(model.api_mode),
            api_key=model.api_key,
            api_host=model.api_host,
            api_path=model.api_path,
            model_id=model.model_id,
            display_name=model.display_name,
            context_window=model.context_window,
            max_output_tokens=model.max_output_tokens,
            is_active=bool(model.is_active),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

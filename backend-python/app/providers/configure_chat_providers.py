"""从本地 secrets 初始化并激活 Chat/LLM Provider 配置。"""

from __future__ import annotations

from pathlib import Path

from app.db.connection import (
    get_runtime_session_factory,
    initialize_runtime_database,
)
from app.db.init_db import SQLiteVecLoader, load_sqlite_vec_extension
from app.entities.provider_config import ProviderConfig
from app.providers.chat_provider_secrets import load_active_chat_provider_config
from app.providers.registry import ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository


def configure_active_chat_provider(
    *,
    secrets_path: str | Path | None = None,
    database_url: str | None = None,
    sqlite_vec_loader: SQLiteVecLoader = load_sqlite_vec_extension,
) -> ProviderConfig:
    """读取 chat_providers.json，将 active provider 幂等写入 DB 并激活。"""

    initialize_runtime_database(
        database_url=database_url,
        sqlite_vec_loader=sqlite_vec_loader,
    )
    config = load_active_chat_provider_config(secrets_path)
    session_factory = get_runtime_session_factory(
        database_url=database_url,
        sqlite_vec_loader=sqlite_vec_loader,
    )

    with session_factory() as session:
        repo = ProviderConfigRepository(session)
        existing = repo.get_by_name(config.name)
        if existing is not None:
            config.id = existing.id
            config.created_at = existing.created_at
        repo.deactivate_all()
        config.is_active = True
        repo.save(config)
        session.commit()

    ProviderRegistry.activate(config)
    return config


def main() -> None:
    config = configure_active_chat_provider()
    print(
        "Chat provider configured: "
        f"name={config.name}, api_mode={config.api_mode.value}, "
        f"model_id={config.model_id}, api_key={config.api_key}"
    )


if __name__ == "__main__":
    main()

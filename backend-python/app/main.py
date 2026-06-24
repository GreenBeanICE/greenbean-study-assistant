# Python 后端应用入口，创建 FastAPI 应用并注册路由。
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api import document_controller, provider_controller, section_controller
from app.api.dependencies import set_session_factory
from app.config.settings import PROVIDER_CONFIGS_PATH
from app.db.connection import create_app_session_factory
from app.db.init_db import load_sqlite_vec_extension
from app.enums.purpose import Purpose
from app.providers.registry import ProviderRegistry
from app.repositories.provider_config_repository import ProviderConfigRepository

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path("data")
_DEFAULT_DATABASE_NAME = "greenbean-study-assistant.sqlite3"
_FALLBACK_EMBEDDING_DIMENSION = 1024


def _resolve_embedding_dimension(repository: ProviderConfigRepository) -> int:
    config = repository.get_active_by_purpose(Purpose.EMBEDDING)
    if config is not None and config.embedding_dimension:
        return config.embedding_dimension
    logger.warning(
        "No active embedding config, using fallback dimension %d",
        _FALLBACK_EMBEDDING_DIMENSION,
    )
    return _FALLBACK_EMBEDDING_DIMENSION


def _restore_active_providers(repository: ProviderConfigRepository) -> None:
    for purpose in (Purpose.CHAT, Purpose.EMBEDDING):
        config = repository.get_active_by_purpose(purpose)
        if config is not None:
            ProviderRegistry.activate(config)
            logger.info("Restored active %s provider: %s", purpose.value, config.name)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    repository = ProviderConfigRepository(PROVIDER_CONFIGS_PATH)
    try:
        embedding_dimension = _resolve_embedding_dimension(repository)
        session_factory = create_app_session_factory(
            database_path=_DEFAULT_DATA_DIR / _DEFAULT_DATABASE_NAME,
            embedding_dimension=embedding_dimension,
            sqlite_vec_loader=load_sqlite_vec_extension,
        )
        set_session_factory(session_factory)
        logger.info("Database session factory configured with dimension %d.", embedding_dimension)
    except Exception as exc:
        logger.warning("Database initialization skipped: %s", exc)
    try:
        _restore_active_providers(repository)
    except Exception as exc:
        logger.warning("Provider restore skipped: %s", exc)
    yield


app = FastAPI(title="Greenbean Study Assistant API", lifespan=lifespan)

app.include_router(document_controller.router, prefix="/api")
app.include_router(section_controller.router, prefix="/api")
app.include_router(provider_controller.router, prefix="/api")

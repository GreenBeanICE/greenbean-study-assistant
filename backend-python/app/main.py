# Python 后端应用入口，创建 FastAPI 应用并注册路由。
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api import document_controller, provider_controller, section_controller
from app.api.dependencies import set_session_factory
from app.db.connection import create_app_session_factory
from app.db.init_db import load_sqlite_vec_extension

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path("data")
_DEFAULT_DATABASE_NAME = "greenbean-study-assistant.sqlite3"
_DEFAULT_EMBEDDING_DIMENSION = 8  # 后续从配置模块读取


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        session_factory = create_app_session_factory(
            database_path=_DEFAULT_DATA_DIR / _DEFAULT_DATABASE_NAME,
            embedding_dimension=_DEFAULT_EMBEDDING_DIMENSION,
            sqlite_vec_loader=load_sqlite_vec_extension,
        )
        set_session_factory(session_factory)
        logger.info("Database session factory configured.")
    except Exception as exc:
        logger.warning("Database initialization skipped: %s", exc)
    yield


app = FastAPI(title="Greenbean Study Assistant API", lifespan=lifespan)

app.include_router(document_controller.router, prefix="/api")
app.include_router(section_controller.router, prefix="/api")
app.include_router(provider_controller.router, prefix="/api")

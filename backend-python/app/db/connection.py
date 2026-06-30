# 数据库连接与运行时 Session 管理。

from collections.abc import Generator

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.config.settings import DatabaseSettings, get_database_settings
from app.db.init_db import (
    DatabaseInitializationResult,
    SQLiteVecLoader,
    initialize_database,
    load_sqlite_vec_extension,
)
from app.db.orm import SessionFactory, create_database_engine, create_session_factory


DEFAULT_EMBEDDING_DIMENSION = 768

_engine: Engine | None = None
_session_factory: SessionFactory | None = None
_database_url: str | None = None


def initialize_runtime_database(
    *,
    database_url: str | None = None,
    sqlite_vec_loader: SQLiteVecLoader = load_sqlite_vec_extension,
    embedding_dimension: int = DEFAULT_EMBEDDING_DIMENSION,
) -> DatabaseInitializationResult:
    """创建运行时数据库目录和 schema；不写入 demo 数据。"""

    settings = get_database_settings(database_url)
    if settings.database_path is None:
        raise ValueError(
            "runtime schema initialization requires a file-backed SQLite database"
        )
    return initialize_database(
        database_path=settings.database_path,
        sqlite_vec_loader=sqlite_vec_loader,
        embedding_dimension=embedding_dimension,
    )


def get_runtime_database_settings(database_url: str | None = None) -> DatabaseSettings:
    return get_database_settings(database_url)


def get_runtime_session_factory(
    *,
    database_url: str | None = None,
    sqlite_vec_loader: SQLiteVecLoader = load_sqlite_vec_extension,
) -> SessionFactory:
    """返回全局 runtime Session factory，避免各模块各自维护 SessionLocal。"""

    global _database_url, _engine, _session_factory

    settings = get_database_settings(database_url)
    if _session_factory is None or _database_url != settings.database_url:
        if _engine is not None:
            _engine.dispose()
        _engine = create_database_engine(
            settings.database_url,
            sqlite_vec_loader=sqlite_vec_loader,
        )
        _session_factory = create_session_factory(_engine)
        _database_url = settings.database_url
    return _session_factory


def get_db_session() -> Generator[Session, None, None]:
    session = get_runtime_session_factory()()
    try:
        yield session
    finally:
        session.close()


def reset_runtime_database_state() -> None:
    """测试辅助：清理进程内 engine/session 缓存。"""

    global _database_url, _engine, _session_factory

    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
    _database_url = None

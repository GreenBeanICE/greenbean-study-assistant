from pathlib import Path
import sqlite3
from typing import Callable

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker


SQLiteVecLoader = Callable[[sqlite3.Connection], None]
SessionFactory = Callable[[], Session]


def create_database_engine(
    database_path: str | Path,
    *,
    sqlite_vec_loader: SQLiteVecLoader,
) -> Engine:
    engine = create_engine(
        URL.create("sqlite+pysqlite", database=str(Path(database_path))),
    )

    @event.listens_for(engine, "connect")
    def initialize_connection(
        dbapi_connection: sqlite3.Connection,
        _connection_record: object,
    ) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys = ON")
        try:
            sqlite_vec_loader(dbapi_connection)
        except Exception:
            pass

    return engine


def create_session_factory(engine: Engine) -> SessionFactory:
    return sessionmaker(bind=engine, expire_on_commit=False)

"""DB connection 聚合入口测试。

验证 create_app_session_factory 在文件模式和 :memory: 模式下都能返回可用 session factory，
以及 create_app_uow 包装 SqlAlchemyUnitOfWork。文件模式间接验证 initialize_database 被调用
（数据库文件被创建），内存模式验证不创建文件。
"""
import sqlite3
from pathlib import Path

import pytest

from app.db.connection import create_app_session_factory, create_app_uow
from app.db.unit_of_work import SqlAlchemyUnitOfWork


def _fake_sqlite_vec_loader(connection: sqlite3.Connection) -> None:
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def _noop_loader(_connection: sqlite3.Connection) -> None:
    pass


@pytest.mark.unit
def test_file_mode_factory_opens_usable_session(tmp_path):
    database_path = tmp_path / "data" / "test.sqlite3"

    factory = create_app_session_factory(
        database_path=database_path,
        embedding_dimension=8,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )

    assert callable(factory)
    with factory() as session:
        assert session is not None
    assert database_path.exists()


@pytest.mark.unit
def test_memory_mode_factory_skips_file_initialization(tmp_path):
    files_before = set(Path(tmp_path).rglob("*"))

    factory = create_app_session_factory(
        database_path=":memory:",
        embedding_dimension=8,
        sqlite_vec_loader=_noop_loader,
    )

    assert callable(factory)
    with factory() as session:
        assert session is not None

    files_after = set(Path(tmp_path).rglob("*"))
    assert files_after == files_before


@pytest.mark.unit
def test_create_app_uow_returns_sqlalchemy_unit_of_work():
    factory = create_app_session_factory(
        database_path=":memory:",
        embedding_dimension=8,
        sqlite_vec_loader=_noop_loader,
    )

    uow = create_app_uow(factory)

    assert isinstance(uow, SqlAlchemyUnitOfWork)

"""数据库连接聚合入口。

组合 init_db.py、orm.py、unit_of_work.py 的现有函数，
为应用启动提供统一的 session factory 和 UOW 创建入口。
不搬迁底层实现，不创建业务 repository。
"""
from pathlib import Path

from app.db.init_db import SQLiteVecLoader, initialize_database
from app.db.orm import SessionFactory, create_database_engine, create_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork

_MEMORY_DATABASE = ":memory:"


def create_app_session_factory(
    database_path: str | Path,
    *,
    embedding_dimension: int,
    sqlite_vec_loader: SQLiteVecLoader,
) -> SessionFactory:
    """创建 app-level session factory。

    文件模式调用 initialize_database() 建表后创建 engine；
    :memory: 模式跳过 initialize_database()，仅创建 engine，用于单元测试。
    """
    if str(database_path) != _MEMORY_DATABASE:
        path = Path(database_path)
        initialize_database(
            data_dir=path.parent,
            database_name=path.name,
            sqlite_vec_loader=sqlite_vec_loader,
            embedding_dimension=embedding_dimension,
        )
    engine = create_database_engine(database_path, sqlite_vec_loader=sqlite_vec_loader)
    return create_session_factory(engine)


def create_app_uow(session_factory: SessionFactory) -> SqlAlchemyUnitOfWork:
    """包装 SqlAlchemyUnitOfWork，供 service 层使用统一事务入口。"""
    return SqlAlchemyUnitOfWork(session_factory)

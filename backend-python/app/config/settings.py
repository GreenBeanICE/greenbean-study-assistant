# 后端运行配置。

from dataclasses import dataclass
import os
from pathlib import Path

from sqlalchemy.engine import make_url


DATABASE_URL_ENV = "DATABASE_URL"
DEFAULT_DATABASE_NAME = "greenbean-study-assistant.sqlite3"


@dataclass(frozen=True)
class DatabaseSettings:
    database_url: str
    database_path: Path | None


def get_project_root() -> Path:
    """返回仓库项目根目录，不依赖当前工作目录。"""

    return Path(__file__).resolve().parents[3]


def get_default_database_path() -> Path:
    """默认 SQLite 数据库绝对路径。"""

    return get_project_root() / "data" / DEFAULT_DATABASE_NAME


def get_database_settings(database_url: str | None = None) -> DatabaseSettings:
    """解析数据库配置，优先使用 DATABASE_URL 环境变量。"""

    resolved_url = database_url or os.environ.get(DATABASE_URL_ENV)
    if resolved_url:
        return DatabaseSettings(
            database_url=resolved_url,
            database_path=_sqlite_file_path_from_url(resolved_url),
        )

    default_path = get_default_database_path()
    return DatabaseSettings(
        database_url=_sqlite_url_from_path(default_path),
        database_path=default_path,
    )


def _sqlite_url_from_path(database_path: Path) -> str:
    return f"sqlite:///{database_path.as_posix()}"


def _sqlite_file_path_from_url(database_url: str) -> Path | None:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        return None
    if not url.database or url.database == ":memory:":
        return None
    return Path(url.database)

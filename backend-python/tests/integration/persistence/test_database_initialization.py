from contextlib import closing
import sqlite3

import pytest

from app.db.init_db import (
    SQLiteVecInitializationError,
    initialize_database,
    load_sqlite_vec_extension,
)
from app.db.orm import create_database_engine, create_session_factory
from app.entities import DocumentRecord
from app.enums import DocumentFileType
from app.repositories.document_repository import DocumentRepository


def load_test_sqlite_vec(connection: sqlite3.Connection) -> None:
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def fail_to_load_sqlite_vec(connection: sqlite3.Connection) -> None:
    raise RuntimeError("sqlite-vec extension missing")


class FakeSQLiteConnection:
    def __init__(self) -> None:
        self.extension_states = []
        self.loaded_extension = None

    def enable_load_extension(self, enabled: bool) -> None:
        self.extension_states.append(enabled)

    def load_extension(self, extension_name: str) -> None:
        self.loaded_extension = extension_name


def test_default_sqlite_vec_loader_enables_loads_and_disables_extension():
    connection = FakeSQLiteConnection()

    load_sqlite_vec_extension(connection)

    assert connection.extension_states == [True, False]
    assert connection.loaded_extension == "sqlite_vec"


def test_first_start_creates_data_dir_and_sqlite_database(tmp_path):
    data_dir = tmp_path / "data"

    result = initialize_database(
        data_dir=data_dir,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )

    assert data_dir.exists()
    assert result.database_path.exists()
    assert result.database_path.parent == data_dir
    assert result.persistence_ready is True
    assert result.sqlite_vec_version == "test-sqlite-vec"


def test_repeated_start_keeps_database_initialization_idempotent(tmp_path):
    data_dir = tmp_path / "data"
    first_result = initialize_database(
        data_dir=data_dir,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )

    document = DocumentRecord(
        workspace_id="workspace_1",
        title="Syllabus",
        original_filename="syllabus.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/syllabus.pdf",
    )
    engine = create_database_engine(
        first_result.database_path,
        sqlite_vec_loader=load_test_sqlite_vec,
    )
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        DocumentRepository(session).save(document)
        session.commit()
    engine.dispose()

    second_result = initialize_database(
        data_dir=data_dir,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )

    engine = create_database_engine(
        second_result.database_path,
        sqlite_vec_loader=load_test_sqlite_vec,
    )
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        persisted = DocumentRepository(session).get_by_id(document.id)
    engine.dispose()

    assert second_result.persistence_ready is True
    assert persisted is not None
    assert persisted.id == document.id
    assert persisted.title == "Syllabus"


def test_successful_initialization_loads_sqlite_vec_and_creates_core_tables(tmp_path):
    result = initialize_database(
        data_dir=tmp_path / "data",
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )

    with closing(sqlite3.connect(result.database_path)) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual table')"
            ).fetchall()
        }

    assert result.sqlite_vec_version == "test-sqlite-vec"
    assert {
        "document_records",
        "document_units",
        "sections",
        "section_unit_links",
        "chunks",
        "analysis_results",
        "chat_sessions",
        "chat_messages",
        "embedding_vectors",
    }.issubset(table_names)


def test_sqlite_vec_load_failure_falls_back_to_plain_sqlite_initialization(tmp_path):
    result = initialize_database(
        data_dir=tmp_path / "data",
        sqlite_vec_loader=fail_to_load_sqlite_vec,
        embedding_dimension=8,
    )

    assert result.persistence_ready is True
    assert result.sqlite_vec_version is None
    assert result.database_path.exists()


def test_sqlite_vec_health_check_failure_falls_back_to_plain_sqlite_initialization(tmp_path):
    result = initialize_database(
        data_dir=tmp_path / "data",
        sqlite_vec_loader=lambda connection: None,
        embedding_dimension=8,
    )

    assert result.persistence_ready is True
    assert result.sqlite_vec_version is None


def test_sqlite_vec_health_check_empty_version_falls_back_to_plain_sqlite(tmp_path):
    def load_empty_version(connection: sqlite3.Connection) -> None:
        connection.create_function("vec_version", 0, lambda: None)

    result = initialize_database(
        data_dir=tmp_path / "data",
        sqlite_vec_loader=load_empty_version,
        embedding_dimension=8,
    )

    assert result.persistence_ready is True
    assert result.sqlite_vec_version is None


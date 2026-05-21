import sqlite3

import pytest

from app.db.init_db import SQLiteVecInitializationError, initialize_database
from app.entities import DocumentRecord
from app.enums import DocumentFileType
from app.repositories.document_repository import DocumentRepository


def load_test_sqlite_vec(connection: sqlite3.Connection) -> None:
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def fail_to_load_sqlite_vec(connection: sqlite3.Connection) -> None:
    raise RuntimeError("sqlite-vec extension missing")


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
    with sqlite3.connect(first_result.database_path) as connection:
        DocumentRepository(connection).save(document)

    second_result = initialize_database(
        data_dir=data_dir,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )

    with sqlite3.connect(second_result.database_path) as connection:
        persisted = DocumentRepository(connection).get_by_id(document.id)

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

    with sqlite3.connect(result.database_path) as connection:
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
        "chunks",
        "analysis_results",
        "chat_sessions",
        "chat_messages",
        "embedding_vectors",
    }.issubset(table_names)


def test_sqlite_vec_load_failure_fails_database_initialization(tmp_path):
    with pytest.raises(SQLiteVecInitializationError, match="sqlite-vec"):
        initialize_database(
            data_dir=tmp_path / "data",
            sqlite_vec_loader=fail_to_load_sqlite_vec,
            embedding_dimension=8,
        )


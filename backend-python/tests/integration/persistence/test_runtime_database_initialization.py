from contextlib import closing
import sqlite3


def load_test_sqlite_vec(connection: sqlite3.Connection) -> None:
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def sqlite_url(database_path) -> str:
    return f"sqlite:///{database_path.as_posix()}"


def table_names(database_path) -> set[str]:
    with closing(sqlite3.connect(database_path)) as connection:
        return {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual table')"
            ).fetchall()
        }


def test_runtime_schema_initialization_creates_required_tables(tmp_path):
    from app.db.connection import initialize_runtime_database

    database_path = tmp_path / "runtime.sqlite3"

    initialize_runtime_database(
        database_url=sqlite_url(database_path),
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )

    assert {
        "document_records",
        "document_units",
        "sections",
        "analysis_results",
    }.issubset(table_names(database_path))


def test_runtime_schema_initialization_is_idempotent_and_preserves_data(tmp_path):
    from app.db.connection import initialize_runtime_database

    database_path = tmp_path / "runtime.sqlite3"
    database_url = sqlite_url(database_path)

    initialize_runtime_database(
        database_url=database_url,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            INSERT INTO document_records(
                id, workspace_id, title, original_filename, file_type,
                file_path, status, page_count, created_at, updated_at
            )
            VALUES(
                'existing-doc', 'workspace-1', 'Existing', 'existing.pdf', 'pdf',
                'data/uploads/existing.pdf', 'parsed', 1,
                '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00'
            )
            """
        )
        connection.commit()

    initialize_runtime_database(
        database_url=database_url,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )

    with closing(sqlite3.connect(database_path)) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM document_records WHERE id = 'existing-doc'"
        ).fetchone()[0]

    assert count == 1

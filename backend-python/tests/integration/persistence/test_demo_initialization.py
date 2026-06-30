from contextlib import closing
import sqlite3


def load_test_sqlite_vec(connection: sqlite3.Connection) -> None:
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def sqlite_url(database_path) -> str:
    return f"sqlite:///{database_path.as_posix()}"


def test_demo_initialization_creates_ch1_1_and_non_empty_units(tmp_path):
    from app.db.demo_init import DEMO_SECTION_ID, initialize_demo_database

    database_path = tmp_path / "demo.sqlite3"

    initialize_demo_database(
        database_url=sqlite_url(database_path),
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )

    with closing(sqlite3.connect(database_path)) as connection:
        section = connection.execute(
            """
            SELECT document_id, title, start_page, end_page
            FROM sections
            WHERE id = ?
            """,
            (DEMO_SECTION_ID,),
        ).fetchone()
        assert section is not None
        document_id, title, start_page, end_page = section
        assert title == "1.1 背景介绍"
        assert start_page == 1
        assert end_page == 1

        unit_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM document_units
            WHERE document_id = ?
              AND page_number BETWEEN ? AND ?
              AND length(trim(text_content)) > 0
            """,
            (document_id, start_page, end_page),
        ).fetchone()[0]

    assert unit_count >= 1


def test_demo_initialization_is_idempotent(tmp_path):
    from app.db.demo_init import DEMO_DOCUMENT_ID, DEMO_SECTION_ID, initialize_demo_database

    database_path = tmp_path / "demo.sqlite3"
    database_url = sqlite_url(database_path)

    for _ in range(2):
        initialize_demo_database(
            database_url=database_url,
            sqlite_vec_loader=load_test_sqlite_vec,
            embedding_dimension=8,
        )

    with closing(sqlite3.connect(database_path)) as connection:
        document_count = connection.execute(
            "SELECT COUNT(*) FROM document_records WHERE id = ?",
            (DEMO_DOCUMENT_ID,),
        ).fetchone()[0]
        section_count = connection.execute(
            "SELECT COUNT(*) FROM sections WHERE id = ?",
            (DEMO_SECTION_ID,),
        ).fetchone()[0]
        unit_count = connection.execute(
            "SELECT COUNT(*) FROM document_units WHERE document_id = ?",
            (DEMO_DOCUMENT_ID,),
        ).fetchone()[0]

    assert document_count == 1
    assert section_count == 1
    assert unit_count == 1

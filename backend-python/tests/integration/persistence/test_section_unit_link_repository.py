import sqlite3

import pytest

from app.db.init_db import initialize_database
from app.db.orm import create_database_engine, create_session_factory
from app.entities import DocumentRecord, DocumentUnit, Section, SectionUnitLink
from app.enums import DocumentFileType
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.repositories.section_repository import SectionRepository
from app.repositories.section_unit_link_repository import SectionUnitLinkRepository


def _load_test_sqlite_vec(connection: sqlite3.Connection) -> None:
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def _make_session_factory(tmp_path):
    result = initialize_database(
        data_dir=tmp_path / "data",
        sqlite_vec_loader=_load_test_sqlite_vec,
        embedding_dimension=8,
    )
    engine = create_database_engine(result.database_path, sqlite_vec_loader=_load_test_sqlite_vec)
    return create_session_factory(engine), engine


def _seed_document_graph(session):
    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit_a = DocumentUnit(document_id=document.id, sequence_index=0, text_content="A")
    unit_b = DocumentUnit(document_id=document.id, sequence_index=1, text_content="B")
    section = Section(document_id=document.id, title="Section 1", level=1, order_index=0)

    DocumentRepository(session).save(document)
    DocumentUnitRepository(session).save(unit_a)
    DocumentUnitRepository(session).save(unit_b)
    SectionRepository(session).save(section)
    return section, unit_a, unit_b


def test_section_unit_link_repository_saves_and_lists_in_order(tmp_path) -> None:
    session_factory, engine = _make_session_factory(tmp_path)

    with session_factory() as session:
        section, unit_a, unit_b = _seed_document_graph(session)
        repo = SectionUnitLinkRepository(session)
        repo.save(SectionUnitLink(section_id=section.id, document_unit_id=unit_b.id, order_index=1))
        repo.save(SectionUnitLink(section_id=section.id, document_unit_id=unit_a.id, order_index=0))
        session.commit()

    with session_factory() as session:
        links = SectionUnitLinkRepository(session).list_by_section(section.id)

    engine.dispose()
    assert [link.document_unit_id for link in links] == [unit_a.id, unit_b.id]


def test_section_unit_link_repository_enforces_uniqueness(tmp_path) -> None:
    session_factory, engine = _make_session_factory(tmp_path)

    with session_factory() as session:
        section, unit_a, _unit_b = _seed_document_graph(session)
        repo = SectionUnitLinkRepository(session)
        repo.save(SectionUnitLink(section_id=section.id, document_unit_id=unit_a.id, order_index=0))
        session.commit()

    with pytest.raises(Exception):
        with session_factory() as session:
            SectionUnitLinkRepository(session).save(
                SectionUnitLink(section_id=section.id, document_unit_id=unit_a.id, order_index=1)
            )
            session.commit()

    with pytest.raises(Exception):
        with session_factory() as session:
            SectionUnitLinkRepository(session).save(
                SectionUnitLink(section_id=section.id, document_unit_id="another-unit", order_index=0)
            )
            session.commit()

    engine.dispose()

import pytest

from app.db.connection import create_app_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.entities import DocumentRecord, DocumentUnit, Section, SectionUnitLink
from app.enums import DocumentFileType
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.repositories.section_repository import SectionRepository
from app.repositories.section_unit_link_repository import SectionUnitLinkRepository
from app.services.section_service import SectionService


def _fake_sqlite_vec_loader(connection):
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


@pytest.fixture
def uow_factory(tmp_path):
    database_path = tmp_path / "data" / "section.sqlite3"
    session_factory = create_app_session_factory(
        database_path=database_path,
        embedding_dimension=8,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )
    return lambda: SqlAlchemyUnitOfWork(session_factory)


def test_build_sections_returns_existing_sections_without_rebuilding(uow_factory) -> None:
    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit = DocumentUnit(document_id=document.id, sequence_index=0, page_number=1, text_content="Text")
    existing = Section(document_id=document.id, title="Existing", level=1, order_index=0)

    with uow_factory() as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(unit)
        SectionRepository(uow.session).save(existing)
        uow.commit()

    service = SectionService(uow_factory=uow_factory)
    sections = service.build_sections(document.id)

    assert len(sections) == 1
    assert sections[0].title == "Existing"


def test_get_section_tree_returns_nested_nodes(uow_factory) -> None:
    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    root = Section(document_id=document.id, title="Root", level=1, order_index=0)
    child = Section(document_id=document.id, parent_section_id=root.id, title="Child", level=2, order_index=1)

    with uow_factory() as uow:
        DocumentRepository(uow.session).save(document)
        SectionRepository(uow.session).save(root)
        SectionRepository(uow.session).save(child)
        uow.commit()

    service = SectionService(uow_factory=uow_factory)
    tree = service.get_section_tree(document.id)

    assert len(tree) == 1
    assert tree[0].title == "Root"
    assert len(tree[0].children) == 1
    assert tree[0].children[0].title == "Child"


def test_get_section_content_uses_link_order(uow_factory) -> None:
    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit_a = DocumentUnit(document_id=document.id, sequence_index=0, page_number=1, text_content="A")
    unit_b = DocumentUnit(document_id=document.id, sequence_index=1, page_number=2, text_content="B")
    section = Section(document_id=document.id, title="S1", level=1, order_index=0)

    with uow_factory() as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(unit_a)
        DocumentUnitRepository(uow.session).save(unit_b)
        SectionRepository(uow.session).save(section)
        SectionUnitLinkRepository(uow.session).save(
            SectionUnitLink(section_id=section.id, document_unit_id=unit_b.id, order_index=0)
        )
        SectionUnitLinkRepository(uow.session).save(
            SectionUnitLink(section_id=section.id, document_unit_id=unit_a.id, order_index=1)
        )
        uow.commit()

    service = SectionService(uow_factory=uow_factory)
    content = service.get_section_content(section.id)

    assert [unit.id for unit in content] == [unit_b.id, unit_a.id]


def test_get_section_content_raises_for_missing_section(uow_factory) -> None:
    service = SectionService(uow_factory=uow_factory)

    with pytest.raises(ValueError, match="Section not found"):
        service.get_section_content("missing")

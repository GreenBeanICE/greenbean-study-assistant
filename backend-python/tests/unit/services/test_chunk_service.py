import pytest

from app.db.connection import create_app_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.entities import DocumentRecord, DocumentUnit
from app.enums import DocumentFileType
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.services.chunk_service import ChunkService


def _fake_sqlite_vec_loader(connection):
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def test_constructor_rejects_overlap_not_smaller_than_chunk_size() -> None:
    with pytest.raises(ValueError, match="overlap_chars"):
        ChunkService(uow_factory=lambda: None, max_chunk_size=100, overlap_chars=100)


def test_split_units_into_chunks_splits_long_text_and_skips_blank() -> None:
    service = ChunkService(uow_factory=lambda: None, max_chunk_size=5, overlap_chars=2)
    units = [
        DocumentUnit(document_id="doc-1", sequence_index=0, text_content="abcdefghij"),
        DocumentUnit(document_id="doc-1", sequence_index=1, text_content="   "),
    ]

    chunks = service.split_units_into_chunks(units)

    assert [chunk.text_content for chunk in chunks] == ["abcde", "defgh", "ghij"]
    assert [(chunk.start_char, chunk.end_char) for chunk in chunks] == [(0, 5), (3, 8), (6, 10)]
    assert all(chunk.document_unit_id == units[0].id for chunk in chunks)


def test_build_chunks_for_document_persists_chunks(tmp_path) -> None:
    database_path = tmp_path / "data" / "chunk.sqlite3"
    session_factory = create_app_session_factory(
        database_path=database_path,
        embedding_dimension=8,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )
    uow_factory = lambda: SqlAlchemyUnitOfWork(session_factory)

    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit = DocumentUnit(document_id=document.id, sequence_index=0, text_content="abcdefgh")

    with uow_factory() as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(unit)
        uow.commit()

    service = ChunkService(uow_factory=uow_factory, max_chunk_size=4, overlap_chars=1)
    created = service.build_chunks_for_document(document.id)

    with uow_factory() as uow:
        persisted = ChunkRepository(uow.session).list_by_document(document.id)

    assert len(created) == 3
    assert [chunk.text_content for chunk in persisted] == ["abcd", "defg", "gh"]

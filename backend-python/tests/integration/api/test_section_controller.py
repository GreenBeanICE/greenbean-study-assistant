import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import set_session_factory
from app.db.connection import create_app_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.entities import DocumentRecord, DocumentUnit
from app.enums import DocumentFileType
from app.main import app
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository


def _fake_sqlite_vec_loader(connection):
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "data" / "section-api.sqlite3"
    session_factory = create_app_session_factory(
        database_path=database_path,
        embedding_dimension=8,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )
    set_session_factory(session_factory)

    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(
            DocumentUnit(document_id=document.id, sequence_index=0, page_number=1, text_content="Page one")
        )
        uow.commit()

    yield TestClient(app), document.id
    set_session_factory(None)


def test_build_tree_and_content_roundtrip(client) -> None:
    test_client, document_id = client
    build_response = test_client.post(f"/api/sections/documents/{document_id}/build")
    assert build_response.status_code == 200
    section_id = build_response.json()["data"][0]["id"]

    tree_response = test_client.get(f"/api/sections/documents/{document_id}/tree")
    assert tree_response.status_code == 200
    assert tree_response.json()["data"][0]["title"] == "Page 1"

    content_response = test_client.get(f"/api/sections/{section_id}/content")
    assert content_response.status_code == 200
    assert content_response.json()["data"][0]["text_content"] == "Page one"


def test_get_section_content_returns_404_for_missing_section(client) -> None:
    test_client, _document_id = client
    response = test_client.get("/api/sections/missing/content")
    assert response.status_code == 404

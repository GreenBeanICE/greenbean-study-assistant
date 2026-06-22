"""DocumentQueryService 测试。

验证 list_by_workspace 和 get_document_detail 的查询行为。
使用文件数据库 + 真实 UOW，确保查询经过真实 repository 读取链路。
"""
import pytest

from app.db.connection import create_app_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.entities import DocumentRecord, DocumentUnit
from app.enums import DocumentFileType
from app.services.document_query_service import DocumentQueryService


def _fake_sqlite_vec_loader(connection):
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


@pytest.fixture
def uow_factory(tmp_path):
    database_path = tmp_path / "data" / "test.sqlite3"
    session_factory = create_app_session_factory(
        database_path=database_path,
        embedding_dimension=8,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )
    return lambda: SqlAlchemyUnitOfWork(session_factory)


def _seed_document_and_units(uow_factory, workspace_id="ws-1"):
    from app.repositories.document_repository import DocumentRepository
    from app.repositories.document_unit_repository import DocumentUnitRepository

    document = DocumentRecord(
        workspace_id=workspace_id,
        title="Test Course",
        original_filename="test.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/test.pdf",
        page_count=2,
    )
    units = [
        DocumentUnit(document_id=document.id, sequence_index=0, text_content="Page 1"),
        DocumentUnit(document_id=document.id, sequence_index=1, text_content="Page 2"),
    ]

    with uow_factory() as uow:
        DocumentRepository(uow.session).save(document)
        for unit in units:
            DocumentUnitRepository(uow.session).save(unit)
        uow.commit()

    return document, units


@pytest.mark.unit
def test_list_by_workspace_returns_only_matching_documents(uow_factory):
    _seed_document_and_units(uow_factory, workspace_id="ws-1")
    _seed_document_and_units(uow_factory, workspace_id="ws-2")

    service = DocumentQueryService(uow_factory=uow_factory)
    results = service.list_by_workspace("ws-1")

    assert len(results) == 1
    assert all(doc.workspace_id == "ws-1" for doc in results)


@pytest.mark.unit
def test_list_by_workspace_returns_empty_when_no_match(uow_factory):
    service = DocumentQueryService(uow_factory=uow_factory)
    results = service.list_by_workspace("nonexistent")
    assert results == []


@pytest.mark.unit
def test_get_document_detail_returns_document_and_units(uow_factory):
    document, units = _seed_document_and_units(uow_factory)

    service = DocumentQueryService(uow_factory=uow_factory)
    detail = service.get_document_detail(document.id)

    assert detail is not None
    assert detail["document"].id == document.id
    assert len(detail["units"]) == 2
    assert [u.sequence_index for u in detail["units"]] == [0, 1]


@pytest.mark.unit
def test_get_document_detail_returns_none_when_not_found(uow_factory):
    service = DocumentQueryService(uow_factory=uow_factory)
    detail = service.get_document_detail("nonexistent")
    assert detail is None

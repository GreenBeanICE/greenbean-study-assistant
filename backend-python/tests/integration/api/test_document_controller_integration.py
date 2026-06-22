"""文档 API 真实依赖集成测试。

不 mock 依赖，走真实 service + repository + DB 链路，
验证上传后列表和详情可查询。覆盖 code review Important 1。
"""
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import set_session_factory
from app.db.connection import create_app_session_factory


def _fake_sqlite_vec_loader(connection):
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


@pytest.fixture
def real_client(tmp_path):
    database_path = tmp_path / "data" / "integration.sqlite3"
    session_factory = create_app_session_factory(
        database_path=database_path,
        embedding_dimension=8,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )
    set_session_factory(session_factory)

    from app.main import app

    yield TestClient(app)

    set_session_factory(None)


@pytest.mark.integration
def test_upload_then_list_then_detail_roundtrip(real_client, text_two_pages_pdf_bytes):
    """上传后列表和详情都能查到，走真实持久化链路。"""
    upload_response = real_client.post(
        "/api/documents/upload",
        files={"file": ("text_two_pages.pdf", text_two_pages_pdf_bytes, "application/pdf")},
    )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()["data"]
    document_id = upload_data["id"]
    assert upload_data["original_filename"] == "text_two_pages.pdf"
    assert upload_data["file_type"] == "pdf"

    list_response = real_client.get(
        "/api/documents", params={"workspace_id": "workspace_1"}
    )
    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert len(list_data) == 1
    assert list_data[0]["id"] == document_id
    assert "file_path" not in list_data[0]

    detail_response = real_client.get(f"/api/documents/{document_id}")
    assert detail_response.status_code == 200
    detail_data = detail_response.json()["data"]
    assert detail_data["document"]["id"] == document_id
    assert len(detail_data["units"]) >= 1


@pytest.mark.integration
def test_get_documents_returns_500_when_session_factory_not_configured():
    """未装配 session factory 时，依赖函数抛 RuntimeError，API 返回 500。"""
    set_session_factory(None)

    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/documents", params={"workspace_id": "workspace_1"})

    assert response.status_code == 500

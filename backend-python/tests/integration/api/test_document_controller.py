"""
文档接口控制器测试，覆盖 document_controller.py 全部逻辑。
使用 FastAPI TestClient 模拟 HTTP 请求。
"""
import asyncio

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.entities import DocumentRecord, DocumentUnit
from app.enums import DocumentFileType, DocumentStatus
from app.main import app
from app.api.dependencies import (
    get_document_query_service,
    get_ingest_service,
    set_session_factory,
)


@pytest.fixture(autouse=True)
def _reset_session_factory():
    yield
    set_session_factory(None)


def _create_test_file(content: bytes, filename: str, content_type: str = "application/octet-stream"):
    return {"file": (filename, content, content_type)}


_FILE_TYPE_BY_SOURCE = {
    "pdf": DocumentFileType.PDF,
    "word": DocumentFileType.DOCX,
    "image": DocumentFileType.IMAGE,
}


def _make_ingest_result(filename: str = "test.pdf", source_type: str = "pdf") -> dict:
    """构造符合 service 返回契约的 mock 结果，含 document_record entity。"""
    record = DocumentRecord(
        workspace_id="workspace_1",
        title=filename.rsplit(".", 1)[0],
        original_filename=filename,
        file_type=_FILE_TYPE_BY_SOURCE.get(source_type, DocumentFileType.OTHER),
        file_path=f"data/uploads/{filename}",
        status=DocumentStatus.PARSED,
        page_count=1,
    )
    return {
        "filename": filename,
        "total_pages": 1,
        "status": "parsed_successfully",
        "page_index_preview": [{"page_number": 1, "char_count": 100, "source_type": source_type}],
        "document_record": record,
        "document_units": [],
    }


def _make_document(**overrides) -> DocumentRecord:
    defaults = {
        "workspace_id": "workspace_1",
        "title": "Test Course",
        "original_filename": "test.pdf",
        "file_type": DocumentFileType.PDF,
        "file_path": "data/uploads/test.pdf",
        "status": DocumentStatus.PARSED,
        "page_count": 1,
    }
    defaults.update(overrides)
    return DocumentRecord(**defaults)


def _install_overrides(mock_service, mock_query_service):
    app.dependency_overrides[get_ingest_service] = lambda: mock_service
    app.dependency_overrides[get_document_query_service] = lambda: mock_query_service


class TestDocumentUpload:
    """文档上传接口测试。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = TestClient(app)
        self.mock_service = MagicMock()
        self.mock_query_service = MagicMock()
        _install_overrides(self.mock_service, self.mock_query_service)
        yield
        app.dependency_overrides.clear()

    @pytest.mark.us25
    def test_upload_pdf_success(self):
        self.mock_service.ingest_document.return_value = _make_ingest_result("test.pdf", "pdf")
        response = self.client.post(
            "/api/documents/upload", files=_create_test_file(b"%PDF-1.4", "test.pdf")
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["original_filename"] == "test.pdf"
        assert data["file_type"] == "pdf"
        assert data["status"] == "parsed"
        assert "file_path" not in data

    @pytest.mark.us25
    def test_upload_docx_success(self):
        self.mock_service.ingest_document.return_value = _make_ingest_result("notes.docx", "word")
        response = self.client.post(
            "/api/documents/upload", files=_create_test_file(b"fake", "notes.docx")
        )

        assert response.status_code == 200
        assert response.json()["data"]["file_type"] == "docx"

    @pytest.mark.us25
    def test_upload_image_success(self):
        self.mock_service.ingest_document.return_value = _make_ingest_result("photo.png", "image")
        response = self.client.post(
            "/api/documents/upload", files=_create_test_file(b"fake", "photo.png")
        )

        assert response.status_code == 200
        assert response.json()["data"]["file_type"] == "image"

    @pytest.mark.us25
    def test_upload_unsupported_format(self):
        response = self.client.post(
            "/api/documents/upload", files=_create_test_file(b"content", "file.ppt")
        )

        assert response.status_code == 400
        assert "暂不支持" in response.json()["detail"]

    @pytest.mark.us25
    def test_upload_empty_filename(self):
        files = {"file": ("", b"content", "application/octet-stream")}
        response = self.client.post("/api/documents/upload", files=files)

        assert response.status_code == 422

    @pytest.mark.us25
    def test_upload_filename_none(self):
        from app.api.document_controller import upload_document

        async def _run():
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = None
            mock_file.read = AsyncMock(return_value=b"content")

            with pytest.raises(HTTPException) as exc_info:
                await upload_document(file=mock_file, ingest_service=self.mock_service)

            assert exc_info.value.status_code == 400
            assert "文件名不能为空" in exc_info.value.detail

        asyncio.run(_run())

    @pytest.mark.us25
    def test_upload_empty_content(self):
        response = self.client.post(
            "/api/documents/upload", files=_create_test_file(b"", "empty.pdf")
        )

        assert response.status_code == 400
        assert "文件内容为空" in response.json()["detail"]

    @pytest.mark.us25
    def test_upload_value_error(self):
        self.mock_service.ingest_document.side_effect = ValueError("业务异常")
        response = self.client.post(
            "/api/documents/upload", files=_create_test_file(b"content", "test.pdf")
        )

        assert response.status_code == 400
        assert "业务异常" in response.json()["detail"]

    @pytest.mark.us25
    def test_upload_internal_error(self):
        self.mock_service.ingest_document.side_effect = Exception("未知错误")
        response = self.client.post(
            "/api/documents/upload", files=_create_test_file(b"content", "test.pdf")
        )

        assert response.status_code == 500
        assert "文件处理失败" in response.json()["detail"]

    @pytest.mark.us25
    def test_upload_jpg_supported(self):
        self.mock_service.ingest_document.return_value = _make_ingest_result("photo.jpg", "image")
        response = self.client.post(
            "/api/documents/upload", files=_create_test_file(b"fake", "photo.jpg")
        )

        assert response.status_code == 200

    @pytest.mark.us25
    def test_upload_jpeg_supported(self):
        self.mock_service.ingest_document.return_value = _make_ingest_result("photo.jpeg", "image")
        response = self.client.post(
            "/api/documents/upload", files=_create_test_file(b"fake", "photo.jpeg")
        )

        assert response.status_code == 200

    @pytest.mark.us25
    def test_upload_webp_supported(self):
        self.mock_service.ingest_document.return_value = _make_ingest_result("image.webp", "image")
        response = self.client.post(
            "/api/documents/upload", files=_create_test_file(b"fake", "image.webp")
        )

        assert response.status_code == 200

    @pytest.mark.us25
    def test_upload_passes_default_workspace_id(self):
        self.mock_service.ingest_document.return_value = _make_ingest_result("test.pdf", "pdf")
        self.client.post(
            "/api/documents/upload", files=_create_test_file(b"content", "test.pdf")
        )

        _, kwargs = self.mock_service.ingest_document.call_args
        assert kwargs.get("workspace_id") == "workspace_1"

    @pytest.mark.us25
    def test_upload_passes_explicit_workspace_id(self):
        self.mock_service.ingest_document.return_value = _make_ingest_result("test.pdf", "pdf")
        self.client.post(
            "/api/documents/upload",
            files=_create_test_file(b"content", "test.pdf"),
            data={"workspace_id": "ws-custom"},
        )

        _, kwargs = self.mock_service.ingest_document.call_args
        assert kwargs.get("workspace_id") == "ws-custom"

    @pytest.mark.us25
    def test_upload_passes_file_hash(self):
        import hashlib

        self.mock_service.ingest_document.return_value = _make_ingest_result("test.pdf", "pdf")
        self.client.post(
            "/api/documents/upload", files=_create_test_file(b"content", "test.pdf")
        )

        _, kwargs = self.mock_service.ingest_document.call_args
        expected_hash = hashlib.sha256(b"content").hexdigest()
        assert kwargs.get("file_hash") == expected_hash


class TestDocumentList:
    """文档列表接口测试。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = TestClient(app)
        self.mock_query_service = MagicMock()
        self.mock_service = MagicMock()
        _install_overrides(self.mock_service, self.mock_query_service)
        yield
        app.dependency_overrides.clear()

    @pytest.mark.us25
    def test_list_documents_returns_items_without_file_path(self):
        self.mock_query_service.list_by_workspace.return_value = [
            _make_document(title="Course A"),
            _make_document(title="Course B"),
        ]
        response = self.client.get("/api/documents", params={"workspace_id": "workspace_1"})

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        assert "file_path" not in data[0]
        titles = [item["title"] for item in data]
        assert "Course A" in titles and "Course B" in titles

    @pytest.mark.us25
    def test_list_documents_returns_empty_when_no_match(self):
        self.mock_query_service.list_by_workspace.return_value = []
        response = self.client.get("/api/documents", params={"workspace_id": "nonexistent"})

        assert response.status_code == 200
        assert response.json()["data"] == []


class TestDocumentDetail:
    """文档详情接口测试。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = TestClient(app)
        self.mock_query_service = MagicMock()
        self.mock_service = MagicMock()
        _install_overrides(self.mock_service, self.mock_query_service)
        yield
        app.dependency_overrides.clear()

    @pytest.mark.us25
    def test_get_detail_returns_document_and_units(self):
        document = _make_document()
        units = [
            DocumentUnit(document_id=document.id, sequence_index=0, text_content="Page 1"),
            DocumentUnit(document_id=document.id, sequence_index=1, text_content="Page 2"),
        ]
        self.mock_query_service.get_document_detail.return_value = {
            "document": document,
            "units": units,
        }
        response = self.client.get(f"/api/documents/{document.id}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["document"]["id"] == document.id
        assert len(data["units"]) == 2

    @pytest.mark.us25
    def test_get_detail_returns_404_when_not_found(self):
        self.mock_query_service.get_document_detail.return_value = None
        response = self.client.get("/api/documents/nonexistent")

        assert response.status_code == 404

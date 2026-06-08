"""
文档接口控制器测试，覆盖 document_controller.py 全部逻辑。
使用 FastAPI TestClient 模拟 HTTP 请求。
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from io import BytesIO

from app.main import app
from app.api.document_controller import get_ingest_service


def _create_test_file(content: bytes, filename: str, content_type: str = "application/octet-stream"):
    """创建测试用 UploadFile 模拟数据 - 使用 (filename, content, content_type) 元组格式"""
    return {"file": (filename, content, content_type)}


class TestDocumentUpload:
    """文档上传接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前重置依赖注入"""
        self.client = TestClient(app)
        self.mock_service = MagicMock()
        
        # 替换依赖注入
        async def mock_get_service():
            return self.mock_service
        
        app.dependency_overrides[get_ingest_service] = mock_get_service
        yield
        app.dependency_overrides.clear()

    def test_upload_pdf_success(self):
        """测试上传 PDF 成功"""
        self.mock_service.ingest_document = AsyncMock(return_value={
            "filename": "test.pdf",
            "total_pages": 1,
            "status": "parsed_successfully",
            "page_index_preview": [{"page_number": 1, "char_count": 100, "source_type": "pdf"}]
        })
        
        files = _create_test_file(b"%PDF-1.4 fake content", "test.pdf")
        response = self.client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "文件上传并解析成功"
        assert data["data"]["filename"] == "test.pdf"

    def test_upload_docx_success(self):
        """测试上传 Word 文档成功"""
        self.mock_service.ingest_document = AsyncMock(return_value={
            "filename": "notes.docx",
            "total_pages": 1,
            "status": "parsed_successfully",
            "page_index_preview": [{"page_number": 1, "char_count": 50, "source_type": "word"}]
        })
        
        files = _create_test_file(b"fake docx content", "notes.docx")
        response = self.client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["filename"] == "notes.docx"

    def test_upload_image_success(self):
        """测试上传图片成功"""
        self.mock_service.ingest_document = AsyncMock(return_value={
            "filename": "photo.png",
            "total_pages": 1,
            "status": "parsed_successfully",
            "page_index_preview": [{"page_number": 1, "char_count": 30, "source_type": "image"}]
        })
        
        files = _create_test_file(b"fake png content", "photo.png")
        response = self.client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200

    def test_upload_unsupported_format(self):
        """测试上传不支持的文件格式"""
        files = _create_test_file(b"content", "file.ppt")
        response = self.client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "暂不支持" in data["detail"]

    def test_upload_empty_filename(self):
        """测试上传文件名为空 - FastAPI 校验返回 422"""
        files = {"file": ("", b"content", "application/octet-stream")}
        response = self.client.post("/api/documents/upload", files=files)
        
        # FastAPI 对空文件名校验返回 422 Unprocessable Entity
        assert response.status_code == 422

    def test_upload_empty_content(self):
        """测试上传空文件"""
        files = _create_test_file(b"", "empty.pdf")
        response = self.client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "文件内容为空" in data["detail"]

    def test_upload_value_error(self):
        """测试 Service 抛出 ValueError"""
        self.mock_service.ingest_document = AsyncMock(side_effect=ValueError("业务异常"))
        
        files = _create_test_file(b"content", "test.pdf")
        response = self.client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 400
        assert "业务异常" in response.json()["detail"]

    def test_upload_internal_error(self):
        """测试 Service 抛出未知异常"""
        self.mock_service.ingest_document = AsyncMock(side_effect=Exception("未知错误"))
        
        files = _create_test_file(b"content", "test.pdf")
        response = self.client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 500
        assert "文件处理失败" in response.json()["detail"]

    def test_upload_jpg_supported(self):
        """测试上传 JPG 图片"""
        self.mock_service.ingest_document = AsyncMock(return_value={
            "filename": "photo.jpg",
            "total_pages": 1,
            "status": "parsed_successfully",
            "page_index_preview": [{"page_number": 1, "char_count": 20, "source_type": "image"}]
        })
        
        files = _create_test_file(b"fake jpg content", "photo.jpg")
        response = self.client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200

    def test_upload_jpeg_supported(self):
        """测试上传 JPEG 图片"""
        self.mock_service.ingest_document = AsyncMock(return_value={
            "filename": "photo.jpeg",
            "total_pages": 1,
            "status": "parsed_successfully",
            "page_index_preview": [{"page_number": 1, "char_count": 20, "source_type": "image"}]
        })
        
        files = _create_test_file(b"fake jpeg content", "photo.jpeg")
        response = self.client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200

    def test_upload_webp_supported(self):
        """测试上传 WEBP 图片"""
        self.mock_service.ingest_document = AsyncMock(return_value={
            "filename": "image.webp",
            "total_pages": 1,
            "status": "parsed_successfully",
            "page_index_preview": [{"page_number": 1, "char_count": 15, "source_type": "image"}]
        })
        
        files = _create_test_file(b"fake webp content", "image.webp")
        response = self.client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200

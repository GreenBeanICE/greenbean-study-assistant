"""
文件工具模块测试，覆盖 file_utils.py 全部函数。
"""
import pytest
from app.utils.file_utils import (
    get_extension,
    is_supported,
    is_image,
    is_document,
    get_mime_type,
)


class TestGetExtension:
    """测试 get_extension 函数"""

    def test_normal_file(self):
        assert get_extension("document.pdf") == ".pdf"
        assert get_extension("image.JPG") == ".jpg"
        assert get_extension("notes.docx") == ".docx"

    def test_no_extension(self):
        assert get_extension("README") == ""

    def test_multiple_dots(self):
        assert get_extension("archive.tar.gz") == ".gz"

    def test_hidden_file(self):
        assert get_extension(".gitkeep") == ""


class TestIsSupported:
    """测试 is_supported 函数"""

    def test_supported_formats(self):
        assert is_supported("file.pdf") is True
        assert is_supported("file.docx") is True
        assert is_supported("file.pptx") is True
        assert is_supported("file.jpg") is True
        assert is_supported("file.jpeg") is True
        assert is_supported("file.png") is True
        assert is_supported("file.webp") is True
        assert is_supported("file.txt") is True
        assert is_supported("file.md") is True

    def test_unsupported_formats(self):
        assert is_supported("file.ppt") is False
        assert is_supported("file.xls") is False
        assert is_supported("file.exe") is False
        assert is_supported("file") is False

    def test_case_insensitive(self):
        assert is_supported("FILE.PDF") is True
        assert is_supported("File.Docx") is True
        assert is_supported("photo.JPG") is True


class TestIsImage:
    """测试 is_image 函数"""

    def test_image_formats(self):
        assert is_image("photo.jpg") is True
        assert is_image("photo.jpeg") is True
        assert is_image("photo.png") is True
        assert is_image("photo.webp") is True

    def test_non_image_formats(self):
        assert is_image("doc.pdf") is False
        assert is_image("doc.docx") is False
        assert is_image("doc.txt") is False


class TestIsDocument:
    """测试 is_document 函数"""

    def test_document_formats(self):
        assert is_document("file.pdf") is True
        assert is_document("file.docx") is True
        assert is_document("file.pptx") is True
        assert is_document("file.txt") is True
        assert is_document("file.md") is True

    def test_non_document_formats(self):
        assert is_document("photo.jpg") is False
        assert is_document("photo.png") is False


class TestGetMimeType:
    """测试 get_mime_type 函数"""

    def test_known_mime_types(self):
        assert get_mime_type("file.pdf") == "application/pdf"
        assert get_mime_type("file.docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert get_mime_type("file.pptx") == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        assert get_mime_type("file.jpg") == "image/jpeg"
        assert get_mime_type("file.jpeg") == "image/jpeg"
        assert get_mime_type("file.png") == "image/png"
        assert get_mime_type("file.webp") == "image/webp"
        assert get_mime_type("file.txt") == "text/plain"
        assert get_mime_type("file.md") == "text/markdown"

    def test_unknown_mime_type(self):
        assert get_mime_type("file.xyz") == "application/octet-stream"
        assert get_mime_type("file") == "application/octet-stream"

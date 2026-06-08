"""
文档摄取服务测试，覆盖 DocumentIngestService 全部逻辑。
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.document_ingest_service import DocumentIngestService


@pytest.mark.asyncio
@pytest.mark.us25
async def test_ingest_pdf_document():
    """测试摄取 PDF 文档"""
    service = DocumentIngestService()
    
    with patch("app.parsers.parser_factory.ParserFactory.get_parser") as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [{
            "page_number": 1,
            "content": "PDF content",
            "char_count": 11,
            "metadata": {"source_type": "pdf"}
        }]
        mock_get_parser.return_value = mock_parser
        
        result = await service.ingest_document("test.pdf", b"fake pdf content")
        
        assert result["filename"] == "test.pdf"
        assert result["total_pages"] == 1
        assert result["status"] == "parsed_successfully"
        assert result["page_index_preview"][0]["source_type"] == "pdf"
        assert result["page_index_preview"][0]["char_count"] == 11


@pytest.mark.asyncio
@pytest.mark.us25
async def test_ingest_word_document():
    """测试摄取 Word 文档"""
    service = DocumentIngestService()
    
    with patch("app.parsers.parser_factory.ParserFactory.get_parser") as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [{
            "page_number": 1,
            "content": "Word content",
            "char_count": 12,
            "metadata": {"source_type": "word"}
        }]
        mock_get_parser.return_value = mock_parser
        
        result = await service.ingest_document("notes.docx", b"fake docx content")
        
        assert result["filename"] == "notes.docx"
        assert result["total_pages"] == 1
        assert result["page_index_preview"][0]["source_type"] == "word"


@pytest.mark.asyncio
@pytest.mark.us25
async def test_ingest_image_document():
    """测试摄取图片文档"""
    service = DocumentIngestService()
    
    with patch("app.parsers.parser_factory.ParserFactory.get_parser") as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [{
            "page_number": 1,
            "content": "OCR text",
            "char_count": 8,
            "metadata": {"source_type": "image"}
        }]
        mock_get_parser.return_value = mock_parser
        
        result = await service.ingest_document("photo.png", b"fake image content")
        
        assert result["filename"] == "photo.png"
        assert result["total_pages"] == 1
        assert result["page_index_preview"][0]["source_type"] == "image"


@pytest.mark.asyncio
@pytest.mark.us25
async def test_ingest_multiple_pages():
    """测试多页文档"""
    service = DocumentIngestService()
    
    with patch("app.parsers.parser_factory.ParserFactory.get_parser") as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            {
                "page_number": 1,
                "content": "Page 1",
                "char_count": 6,
                "metadata": {"source_type": "pdf"}
            },
            {
                "page_number": 2,
                "content": "Page 2",
                "char_count": 6,
                "metadata": {"source_type": "pdf"}
            },
        ]
        mock_get_parser.return_value = mock_parser
        
        result = await service.ingest_document("multi.pdf", b"fake multi page content")
        
        assert result["total_pages"] == 2
        assert len(result["page_index_preview"]) == 2
        assert result["page_index_preview"][0]["page_number"] == 1
        assert result["page_index_preview"][1]["page_number"] == 2


@pytest.mark.asyncio
@pytest.mark.us25
async def test_ingest_unsupported_format():
    """测试不支持的文件格式"""
    service = DocumentIngestService()
    
    with patch("app.parsers.parser_factory.ParserFactory.get_parser") as mock_get_parser:
        mock_get_parser.side_effect = ValueError("暂不支持文件格式: file.ppt")
        
        with pytest.raises(ValueError, match="暂不支持文件格式"):
            await service.ingest_document("file.ppt", b"content")


@pytest.mark.asyncio
@pytest.mark.us25
async def test_ingest_empty_content():
    """测试空内容文档"""
    service = DocumentIngestService()
    
    with patch("app.parsers.parser_factory.ParserFactory.get_parser") as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [{
            "page_number": 1,
            "content": "",
            "char_count": 0,
            "metadata": {"source_type": "pdf"}
        }]
        mock_get_parser.return_value = mock_parser
        
        result = await service.ingest_document("empty.pdf", b"")
        
        assert result["total_pages"] == 1
        assert result["page_index_preview"][0]["char_count"] == 0


@pytest.mark.asyncio
@pytest.mark.us25
async def test_ingest_no_metadata():
    """测试解析结果没有 metadata 的情况"""
    service = DocumentIngestService()
    
    with patch("app.parsers.parser_factory.ParserFactory.get_parser") as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [{
            "page_number": 1,
            "content": "No metadata",
            "char_count": 11,
            # 没有 metadata 字段
        }]
        mock_get_parser.return_value = mock_parser
        
        result = await service.ingest_document("test.pdf", b"content")
        
        assert result["total_pages"] == 1
        # 没有 metadata 时，page_index_preview 中不包含 source_type 字段
        assert "source_type" not in result["page_index_preview"][0]

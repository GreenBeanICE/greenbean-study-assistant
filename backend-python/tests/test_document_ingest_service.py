# 文档摄取服务测试占位文件，后续用于验证文档摄取流程。
# backend-python/tests/test_document_ingest_service.py
import pytest
from unittest.mock import MagicMock, patch
from app.services.document_ingest_service import DocumentIngestService

# 告诉 pytest 这个文件里的用例都支持异步 async 语法
pytestmark = pytest.mark.asyncio

async def test_document_ingest_pipeline_success():
    """
    测试 IngestService 的流水线是否能正常串联工厂与解析器，并输出 PageIndex 预览
    """
    service = DocumentIngestService()
    
    # 模拟一个解析器实例及其返回的单页骨架
    mock_parser = MagicMock()
    mock_parser.parse.return_value = [
        {"page_number": 1, "content": "Mocked Content", "char_count": 14}
    ]
    
    # 拦截工厂静态方法，让它直接返回我们的伪解析器
    with patch("app.parsers.parser_factory.ParserFactory.get_parser", return_value=mock_parser):
        
        # 触发业务流水线
        result = await service.ingest_document("test_course.pdf", b"fake_bytes")
        
        # 验证返回的业务结构
        assert result["filename"] == "test_course.pdf"
        assert result["total_pages"] == 1
        assert result["status"] == "parsed_successfully"
        assert result["page_index_preview"][0]["page_number"] == 1
        assert result["page_index_preview"][0]["char_count"] == 14
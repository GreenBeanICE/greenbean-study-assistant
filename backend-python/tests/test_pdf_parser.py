# PDF 解析器测试占位文件，后续用于验证 PDF 解析逻辑。
# backend-python/tests/test_pdf_parser.py
import pytest
from unittest.mock import MagicMock, patch
from app.parsers.pdf_parser import PDFParser

@pytest.mark.us25
def test_pdf_parser_extract_text_success():
    """
    测试 PDFParser 是否能正确循环读取页码并统计字符数
    """
    parser = PDFParser()
    
    # 模拟 fitz.open 返回的 document 对象
    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        
        # 模拟 PDF一共有 2 页
        mock_doc.__len__.return_value = 2
        
        # 模拟每一页提取出来的文本
        mock_page_1 = MagicMock()
        mock_page_1.get_text.return_value = "Welcome to Greenbean"
        
        mock_page_2 = MagicMock()
        mock_page_2.get_text.return_value = "MIAGE M1 Dev Project"
        
        # 让 load_page 按顺序返回这两页
        mock_doc.load_page.side_effect = [mock_page_1, mock_page_2]
        
        # 执行解析
        result = parser.parse(b"fake pdf binary stream")
        
        # 断言校验
        assert len(result) == 2
        assert result[0]["page_number"] == 1
        assert result[0]["char_count"] == 20
        assert result[0]["parser_name"] == "PDFParser"
        assert result[0]["parser_version"] == "1.0.0"
        assert result[0]["metadata"]["source_type"] == "pdf"
        assert result[0]["metadata"]["headings"] == []
        assert result[0]["metadata"]["paragraphs_count"] == 0
        assert result[1]["page_number"] == 2
        assert result[1]["char_count"] == 20
        assert result[1]["parser_name"] == "PDFParser"
        assert result[1]["parser_version"] == "1.0.0"
        
        # 确保 doc.close() 安全关闭了流
        mock_doc.close.assert_called_once()
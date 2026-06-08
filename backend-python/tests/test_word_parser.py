"""
Word 解析器测试文件，用于验证 Word 文档解析逻辑。
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from app.parsers.word_parser import WordParser


def test_word_parser_extract_paragraphs():
    """
    测试 WordParser 是否能正确提取段落文本。
    """
    parser = WordParser()
    
    # 模拟 WordParser 模块中导入的 Document
    with patch("app.parsers.word_parser.Document") as mock_document:
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        # 模拟段落
        mock_para_1 = MagicMock()
        mock_para_1.text = "这是第一段文本"
        mock_para_1.style.name = "Normal"
        
        mock_para_2 = MagicMock()
        mock_para_2.text = "这是第二段文本"
        mock_para_2.style.name = "Normal"
        
        mock_doc.paragraphs = [mock_para_1, mock_para_2]
        mock_doc.tables = []
        
        # 执行解析
        result = parser.parse(b"fake docx binary stream")
        
        # 断言校验
        assert len(result) == 1
        assert result[0]["page_number"] == 1
        assert "第一段文本" in result[0]["content"]
        assert "第二段文本" in result[0]["content"]
        assert result[0]["metadata"]["source_type"] == "word"
        assert result[0]["metadata"]["paragraphs_count"] == 2
        assert result[0]["metadata"]["tables_count"] == 0


def test_word_parser_extract_tables():
    """
    测试 WordParser 是否能正确提取表格文本。
    """
    parser = WordParser()
    
    with patch("app.parsers.word_parser.Document") as mock_document:
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        mock_doc.paragraphs = []
        
        # 模拟表格
        mock_cell_1 = MagicMock()
        mock_cell_1.text = "姓名"
        mock_cell_2 = MagicMock()
        mock_cell_2.text = "年龄"
        mock_cell_3 = MagicMock()
        mock_cell_3.text = "张三"
        mock_cell_4 = MagicMock()
        mock_cell_4.text = "25"
        
        mock_row_1 = MagicMock()
        mock_row_1.cells = [mock_cell_1, mock_cell_2]
        mock_row_2 = MagicMock()
        mock_row_2.cells = [mock_cell_3, mock_cell_4]
        
        mock_table = MagicMock()
        mock_table.rows = [mock_row_1, mock_row_2]
        mock_doc.tables = [mock_table]
        
        # 执行解析
        result = parser.parse(b"fake docx binary stream")
        
        # 断言校验
        assert len(result) == 1
        assert "姓名" in result[0]["content"]
        assert "年龄" in result[0]["content"]
        assert "张三" in result[0]["content"]
        assert "25" in result[0]["content"]
        assert result[0]["metadata"]["tables_count"] == 1


def test_word_parser_headings():
    """
    测试 WordParser 是否能正确识别标题层级。
    """
    parser = WordParser()
    
    with patch("app.parsers.word_parser.Document") as mock_document:
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        # 模拟带标题的段落
        mock_heading_1 = MagicMock()
        mock_heading_1.text = "第一章 引言"
        mock_heading_1.style.name = "Heading 1"
        
        mock_heading_2 = MagicMock()
        mock_heading_2.text = "1.1 研究背景"
        mock_heading_2.style.name = "Heading 2"
        
        mock_para = MagicMock()
        mock_para.text = "这是一些正文内容"
        mock_para.style.name = "Normal"
        
        mock_doc.paragraphs = [mock_heading_1, mock_heading_2, mock_para]
        mock_doc.tables = []
        
        # 执行解析
        result = parser.parse(b"fake docx binary stream")
        
        # 断言校验
        headings = result[0]["metadata"]["headings"]
        assert len(headings) == 2
        assert headings[0]["level"] == 1
        assert headings[0]["text"] == "第一章 引言"
        assert headings[1]["level"] == 2
        assert headings[1]["text"] == "1.1 研究背景"


def test_word_parser_empty_document():
    """
    测试 WordParser 处理空文档的边界情况。
    """
    parser = WordParser()
    
    with patch("app.parsers.word_parser.Document") as mock_document:
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        mock_doc.paragraphs = []
        mock_doc.tables = []
        
        # 执行解析
        result = parser.parse(b"fake docx binary stream")
        
        # 断言校验
        assert len(result) == 1
        assert result[0]["content"] == ""
        assert result[0]["char_count"] == 0
        assert result[0]["metadata"]["paragraphs_count"] == 0
        assert result[0]["metadata"]["tables_count"] == 0

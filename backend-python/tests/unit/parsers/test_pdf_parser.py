# PDF 解析器测试
# backend-python/tests/unit/parsers/test_pdf_parser.py
import pytest
from unittest.mock import MagicMock, patch, call
from app.parsers.pdf_parser import PDFParser


@pytest.mark.us25
def test_pdf_parser_extracts_structured_blocks():
    """PDFParser 应该从每页提取结构化 blocks，包含 bbox/font_size/is_bold 等信息。"""
    parser = PDFParser()

    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.rect.width = 595.0
        mock_page.rect.height = 842.0

        # 模拟 PyMuPDF 的 dict 模式输出
        dict_output = {
            "blocks": [
                {
                    "type": 0,
                    "bbox": (72.0, 96.0, 300.0, 120.0),
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "1. Introduction",
                                    "font": "Helvetica-Bold",
                                    "size": 18.0,
                                    "bbox": (72.0, 96.0, 300.0, 120.0)
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": 0,
                    "bbox": (72.0, 130.0, 500.0, 200.0),
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "This is content.",
                                    "font": "Helvetica",
                                    "size": 10.5,
                                    "bbox": (72.0, 130.0, 500.0, 150.0)
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_page.get_text.side_effect = [dict_output, "1. Introduction\nThis is content."]
        mock_doc.load_page.return_value = mock_page

        result = parser.parse(b"fake pdf")

        assert len(result) == 1
        page = result[0]

        # 验证结构化 blocks
        assert "blocks" in page
        blocks = page["blocks"]
        assert len(blocks) == 2
        assert blocks[0]["text"] == "1. Introduction"
        assert blocks[0]["bbox"] == [72.0, 96.0, 300.0, 120.0]
        assert blocks[0]["font_size"] == 18.0
        assert blocks[0]["font_name"] == "Helvetica-Bold"
        assert blocks[0]["is_bold"] is True
        assert blocks[1]["text"] == "This is content."
        assert blocks[1]["is_bold"] is False


@pytest.mark.us25
def test_pdf_parser_detects_heading_candidates():
    """PDFParser 应该识别字号明显更大且带编号的文本为 heading 候选。"""
    parser = PDFParser()

    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.rect.width = 595.0
        mock_page.rect.height = 842.0

        # 主字号 10.5，标题字号 18.0
        dict_output = {
            "blocks": [
                {
                    "type": 0,
                    "bbox": (72.0, 96.0, 300.0, 120.0),
                    "lines": [{"spans": [{"text": "1. Introduction", "font": "Helvetica-Bold", "size": 18.0, "bbox": (72.0, 96.0, 300.0, 120.0)}]}]
                },
                {
                    "type": 0,
                    "bbox": (72.0, 130.0, 500.0, 200.0),
                    "lines": [{"spans": [{"text": "This is content.", "font": "Helvetica", "size": 10.5, "bbox": (72.0, 130.0, 500.0, 150.0)}]}]
                }
            ]
        }
        mock_page.get_text.side_effect = [dict_output, "1. Introduction\nThis is content."]
        mock_doc.load_page.return_value = mock_page

        result = parser.parse(b"fake pdf")

        headings = result[0]["metadata"]["headings"]
        assert len(headings) == 1
        assert headings[0]["title"] == "1. Introduction"
        assert headings[0]["level"] == 1
        assert headings[0]["confidence"] > 0.5
        assert headings[0]["source_block_id"] == "b-0"
        assert headings[0]["numbering_pattern"] == "decimal"


@pytest.mark.us25
@pytest.mark.parametrize(
    ("heading_text", "expected_level"),
    [
        ("1 Introduction", 1),
        ("1. Introduction", 1),
        ("1.1 Background", 2),
        ("1.1.1 Details", 3),
        ("1.1.1.1 Deep Dive", 4),
        ("1. Étude de cas", 1),
    ],
)
def test_pdf_parser_detects_decimal_heading_levels(heading_text: str, expected_level: int):
    """PDFParser 应该按十进制编号深度输出标题层级。"""
    parser = PDFParser()

    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.rect.width = 595.0
        mock_page.rect.height = 842.0
        dict_output = {
            "blocks": [
                {
                    "type": 0,
                    "bbox": (72.0, 96.0, 300.0, 120.0),
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": heading_text,
                                    "font": "Helvetica-Bold",
                                    "size": 18.0,
                                    "bbox": (72.0, 96.0, 300.0, 120.0),
                                }
                            ]
                        }
                    ],
                },
                {
                    "type": 0,
                    "bbox": (72.0, 130.0, 500.0, 200.0),
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Body text.",
                                    "font": "Helvetica",
                                    "size": 10.5,
                                    "bbox": (72.0, 130.0, 500.0, 150.0),
                                }
                            ]
                        }
                    ],
                },
            ]
        }
        mock_page.get_text.side_effect = [dict_output, f"{heading_text}\nBody text."]
        mock_doc.load_page.return_value = mock_page

        result = parser.parse(b"fake pdf")

    headings = result[0]["metadata"]["headings"]
    assert len(headings) == 1
    assert headings[0]["title"] == heading_text
    assert headings[0]["level"] == expected_level
    assert headings[0]["numbering_pattern"] == "decimal"


@pytest.mark.us25
@pytest.mark.parametrize(
    "body_text",
    [
        "1 item in the list",
        "2024 results",
        "1.1 item in the list",
        "1.1 million users",
        "3.14 is pi",
    ],
)
def test_pdf_parser_does_not_treat_plain_numeric_short_text_as_heading(body_text: str):
    """普通数字短句不应该仅因数字前缀被识别为 heading。"""
    parser = PDFParser()

    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.rect.width = 595.0
        mock_page.rect.height = 842.0
        dict_output = {
            "blocks": [
                {
                    "type": 0,
                    "bbox": (72.0, 130.0, 500.0, 200.0),
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": body_text,
                                    "font": "Helvetica",
                                    "size": 10.5,
                                    "bbox": (72.0, 130.0, 500.0, 150.0),
                                }
                            ]
                        }
                    ],
                }
            ]
        }
        mock_page.get_text.side_effect = [dict_output, body_text]
        mock_doc.load_page.return_value = mock_page

        result = parser.parse(b"fake pdf")

    assert result[0]["metadata"]["headings"] == []


@pytest.mark.us25
def test_pdf_parser_preserves_chinese_chapter_heading_level():
    """PDFParser 应该保留中文章节标题的 fallback 层级规则。"""
    parser = PDFParser()

    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.rect.width = 595.0
        mock_page.rect.height = 842.0
        dict_output = {
            "blocks": [
                {
                    "type": 0,
                    "bbox": (72.0, 96.0, 300.0, 120.0),
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "第1章 绪论",
                                    "font": "Helvetica-Bold",
                                    "size": 18.0,
                                    "bbox": (72.0, 96.0, 300.0, 120.0),
                                }
                            ]
                        }
                    ],
                }
            ]
        }
        mock_page.get_text.side_effect = [dict_output, "第1章 绪论"]
        mock_doc.load_page.return_value = mock_page

        result = parser.parse(b"fake pdf")

    headings = result[0]["metadata"]["headings"]
    assert len(headings) == 1
    assert headings[0]["title"] == "第1章 绪论"
    assert headings[0]["level"] == 1
    assert headings[0]["numbering_pattern"] == "chapter_zh"

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

        # 模拟 PyMuPDF dict 模式输出
        empty_dict_output = {"blocks": []}

        # 模拟每一页提取出来的文本
        mock_page_1 = MagicMock()
        mock_page_1.rect.width = 595.0
        mock_page_1.rect.height = 842.0
        mock_page_1.get_text.side_effect = [empty_dict_output, "Welcome to Greenbean"]

        mock_page_2 = MagicMock()
        mock_page_2.rect.width = 595.0
        mock_page_2.rect.height = 842.0
        mock_page_2.get_text.side_effect = [empty_dict_output, "MIAGE M1 Dev Project"]

        # 让 load_page 按顺序返回这两页
        mock_doc.load_page.side_effect = [mock_page_1, mock_page_2]

        # 执行解析
        result = parser.parse(b"fake pdf binary stream")

        # 断言校验
        assert len(result) == 2
        assert result[0]["page_number"] == 1
        assert result[0]["char_count"] == 20
        assert result[0]["parser_name"] == "PDFParser"
        assert result[0]["parser_version"] == "2.0.0"
        assert result[0]["metadata"]["source_type"] == "pdf"
        assert result[0]["metadata"]["headings"] == []
        assert result[0]["metadata"]["paragraphs_count"] == 1
        assert result[1]["page_number"] == 2
        assert result[1]["char_count"] == 20
        assert result[1]["parser_name"] == "PDFParser"
        assert result[1]["parser_version"] == "2.0.0"

        # 确保 doc.close() 安全关闭了流
        mock_doc.close.assert_called_once()

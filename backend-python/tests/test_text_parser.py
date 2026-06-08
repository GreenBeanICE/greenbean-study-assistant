"""
纯文本解析器测试，覆盖 TextParser 全部逻辑。
"""
import pytest
from app.parsers.text_parser import TextParser


class TestTextParser:
    """TextParser 解析器测试"""

    def test_parse_utf8_text(self):
        """测试解析 UTF-8 编码的纯文本"""
        parser = TextParser()
        content = "Hello World\n\nThis is a test.".encode("utf-8")
        result = parser.parse(content)
        
        assert len(result) == 1
        assert result[0]["page_number"] == 1
        assert result[0]["content"] == "Hello World\n\nThis is a test."
        assert result[0]["char_count"] == 28
        assert result[0]["metadata"]["source_type"] == "text"
        assert result[0]["metadata"]["is_markdown"] is False
        assert result[0]["metadata"]["paragraphs_count"] == 2

    def test_parse_gbk_text(self):
        """测试解析 GBK 编码的中文文本"""
        parser = TextParser()
        content = "你好世界\n\n这是一段测试。".encode("gbk")
        result = parser.parse(content)
        
        assert len(result) == 1
        assert "你好世界" in result[0]["content"]
        assert result[0]["metadata"]["source_type"] == "text"

    def test_parse_markdown(self):
        """测试解析 Markdown 文件"""
        parser = TextParser()
        content = """# 第一章

这是第一章的内容。

## 1.1 背景

这是背景介绍。

```python
print("hello")
```"""
        result = parser.parse(content.encode("utf-8"))
        
        assert len(result) == 1
        assert result[0]["metadata"]["is_markdown"] is True
        assert len(result[0]["metadata"]["headings"]) == 2
        assert result[0]["metadata"]["headings"][0] == {"level": 1, "text": "第一章"}
        assert result[0]["metadata"]["headings"][1] == {"level": 2, "text": "1.1 背景"}

    def test_parse_empty_text(self):
        """测试解析空文本"""
        parser = TextParser()
        result = parser.parse(b"")
        
        assert len(result) == 1
        assert result[0]["content"] == ""
        assert result[0]["char_count"] == 0
        assert result[0]["metadata"]["paragraphs_count"] == 0

    def test_parse_single_line(self):
        """测试解析单行文本"""
        parser = TextParser()
        result = parser.parse(b"Just one line")
        
        assert len(result) == 1
        assert result[0]["content"] == "Just one line"
        assert result[0]["char_count"] == 13
        assert result[0]["metadata"]["paragraphs_count"] == 1

    def test_parse_markdown_without_headings(self):
        """测试 Markdown 文件没有标题的情况"""
        parser = TextParser()
        content = "This is plain text.\n\nNo headings here.".encode("utf-8")
        result = parser.parse(content)
        
        assert result[0]["metadata"]["is_markdown"] is False
        assert result[0]["metadata"]["headings"] == []

"""
PPT 解析器测试，覆盖 PptParser 基本逻辑。
需要 python-pptx 库生成测试用的 .pptx 文件。
"""
import io
import pytest
from pptx import Presentation
from pptx.util import Inches
from app.parsers.ppt_parser import PptParser


def create_test_pptx(slides_count: int = 2) -> bytes:
    """生成测试用的 .pptx 文件字节流"""
    prs = Presentation()
    
    for i in range(slides_count):
        slide_layout = prs.slide_layouts[0]  # 标题+内容布局
        slide = prs.slides.add_slide(slide_layout)
        
        # 标题占位符 (idx=0)
        title = slide.shapes.title
        title.text = f"第{i+1}章 测试标题"
        
        # 内容占位符 (idx=1)
        content = slide.placeholders[1]
        content.text = f"这是第{i+1}页的内容。\n包含多行文本。"
    
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.read()


class TestPptParser:
    """PptParser 解析器测试"""

    def test_parse_pptx(self):
        """测试解析 .pptx 文件"""
        parser = PptParser()
        content = create_test_pptx(slides_count=2)
        result = parser.parse(content)
        
        assert len(result) == 2
        assert result[0]["page_number"] == 1
        assert result[1]["page_number"] == 2
        assert "第1章 测试标题" in result[0]["content"]
        assert "第2章 测试标题" in result[1]["content"]
        assert result[0]["metadata"]["source_type"] == "ppt"
        assert result[1]["metadata"]["source_type"] == "ppt"

    def test_parse_single_slide(self):
        """测试解析单页 PPT"""
        parser = PptParser()
        content = create_test_pptx(slides_count=1)
        result = parser.parse(content)
        
        assert len(result) == 1
        assert result[0]["page_number"] == 1
        assert result[0]["char_count"] > 0
        assert len(result[0]["metadata"]["headings"]) > 0

    def test_parse_empty_pptx(self):
        """测试解析空 PPT（无幻灯片）"""
        parser = PptParser()
        prs = Presentation()
        buf = io.BytesIO()
        prs.save(buf)
        buf.seek(0)
        result = parser.parse(buf.read())
        
        assert len(result) == 0

    def test_parse_metadata_structure(self):
        """测试解析结果的元数据结构"""
        parser = PptParser()
        content = create_test_pptx(slides_count=1)
        result = parser.parse(content)
        
        metadata = result[0]["metadata"]
        assert "source_type" in metadata
        assert "headings" in metadata
        assert "shapes_count" in metadata
        assert "paragraphs_count" in metadata
        assert metadata["source_type"] == "ppt"

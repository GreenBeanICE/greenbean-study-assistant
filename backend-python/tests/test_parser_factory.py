"""
解析器工厂测试文件，用于验证工厂路由逻辑。
"""
import pytest
from app.parsers.parser_factory import ParserFactory
from app.parsers.pdf_parser import PDFParser
from app.parsers.word_parser import WordParser
from app.parsers.ppt_parser import PptParser
from app.parsers.image_ocr_parser import ImageOCRParser
from app.parsers.text_parser import TextParser


class TestParserFactory:
    """ParserFactory 路由测试"""

    def test_factory_returns_pdf_parser(self):
        """测试 .pdf 文件返回 PDFParser"""
        parser = ParserFactory.get_parser("course.pdf")
        assert isinstance(parser, PDFParser)

    def test_factory_returns_word_parser(self):
        """测试 .docx 文件返回 WordParser"""
        parser = ParserFactory.get_parser("notes.docx")
        assert isinstance(parser, WordParser)

    def test_factory_returns_ppt_parser(self):
        """测试 .pptx 文件返回 PptParser"""
        parser = ParserFactory.get_parser("slides.pptx")
        assert isinstance(parser, PptParser)

    def test_factory_returns_text_parser_txt(self):
        """测试 .txt 文件返回 TextParser"""
        parser = ParserFactory.get_parser("notes.txt")
        assert isinstance(parser, TextParser)

    def test_factory_returns_text_parser_md(self):
        """测试 .md 文件返回 TextParser"""
        parser = ParserFactory.get_parser("readme.md")
        assert isinstance(parser, TextParser)

    def test_factory_returns_image_parser_jpg(self):
        """测试 .jpg 文件返回 ImageOCRParser"""
        parser = ParserFactory.get_parser("photo.jpg")
        assert isinstance(parser, ImageOCRParser)

    def test_factory_returns_image_parser_jpeg(self):
        """测试 .jpeg 文件返回 ImageOCRParser"""
        parser = ParserFactory.get_parser("photo.jpeg")
        assert isinstance(parser, ImageOCRParser)

    def test_factory_returns_image_parser_png(self):
        """测试 .png 文件返回 ImageOCRParser"""
        parser = ParserFactory.get_parser("screenshot.png")
        assert isinstance(parser, ImageOCRParser)

    def test_factory_returns_image_parser_webp(self):
        """测试 .webp 文件返回 ImageOCRParser"""
        parser = ParserFactory.get_parser("image.webp")
        assert isinstance(parser, ImageOCRParser)

    def test_factory_case_insensitive(self):
        """测试文件名大小写不敏感"""
        parser = ParserFactory.get_parser("COURSE.PDF")
        assert isinstance(parser, PDFParser)
        
        parser = ParserFactory.get_parser("Notes.DOCX")
        assert isinstance(parser, WordParser)
        
        parser = ParserFactory.get_parser("Slides.PPTX")
        assert isinstance(parser, PptParser)
        
        parser = ParserFactory.get_parser("Photo.JPG")
        assert isinstance(parser, ImageOCRParser)
        
        parser = ParserFactory.get_parser("README.TXT")
        assert isinstance(parser, TextParser)

    def test_factory_unsupported_format(self):
        """测试不支持的文件格式抛出 ValueError"""
        with pytest.raises(ValueError, match="暂不支持文件格式"):
            ParserFactory.get_parser("file.xyz")
        
        with pytest.raises(ValueError, match="暂不支持文件格式"):
            ParserFactory.get_parser("file")

    def test_factory_old_ppt_unsupported(self):
        """测试旧版 .ppt 格式返回转换提示"""
        with pytest.raises(ValueError, match="请转换为 .pptx"):
            ParserFactory.get_parser("slides.ppt")

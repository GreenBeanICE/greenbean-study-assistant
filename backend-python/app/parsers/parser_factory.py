"""
解析器工厂，用于按文件类型选择合适解析器。
"""
from app.parsers.pdf_parser import PDFParser
from app.parsers.word_parser import WordParser
from app.parsers.ppt_parser import PptParser
from app.parsers.image_ocr_parser import ImageOCRParser
from app.parsers.text_parser import TextParser


class ParserFactory:
    @staticmethod
    def get_parser(filename: str):
        """
        根据文件后缀名，自动匹配并返回对应的解析器实例。
        
        :param filename: 文件名（含扩展名）
        :return: 解析器实例
        :raises ValueError: 不支持的格式
        """
        fn_lower = filename.lower()
        
        if fn_lower.endswith('.pdf'):
            return PDFParser()
        
        elif fn_lower.endswith('.docx'):
            return WordParser()
        
        elif fn_lower.endswith(('.pptx',)):
            return PptParser()
        
        elif fn_lower.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            return ImageOCRParser()
        
        elif fn_lower.endswith(('.txt', '.md')):
            return TextParser()
        
        elif fn_lower.endswith(('.ppt',)):
            raise ValueError(
                f"暂不支持文件格式: {filename}。"
                f".ppt 是旧版 PowerPoint 格式（97-2003），请转换为 .pptx 后再上传。"
                f"当前支持: PDF(.pdf), Word(.docx), PPT(.pptx), 纯文本(.txt/.md), 图片(.jpg/.jpeg/.png/.webp)"
            )
        
        else:
            raise ValueError(
                f"暂不支持文件格式: {filename}。"
                f"当前支持: PDF(.pdf), Word(.docx), PPT(.pptx), 纯文本(.txt/.md), 图片(.jpg/.jpeg/.png/.webp)"
            )

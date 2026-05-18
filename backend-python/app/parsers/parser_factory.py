# 解析器工厂占位文件，后续用于按文件类型选择合适解析器。
# backend-python/app/parsers/parser_factory.py
from app.parsers.pdf_parser import PDFParser
# from app.parsers.text_parser import TextParser  # 后续扩展时解锁
# from app.parsers.image_ocr_parser import ImageOCRParser # 后续扩展时解锁

class ParserFactory:
    @staticmethod
    def get_parser(filename: str):
        """
        根据文件后缀名，自动匹配并返回对应的解析器实例
        """
        fn_lower = filename.lower()
        
        if fn_lower.endswith('.pdf'):
            return PDFParser()
        
        # 预留后期的 Word、PPT、图片 OCR 扩展接口
        # elif fn_lower.endswith('.docx') or fn_lower.endswith('.doc'):
        #     return WordParser()
        # elif fn_lower.endswith(('.png', '.jpg', '.jpeg')):
        #     return ImageOCRParser()
            
        else:
            raise ValueError(f"暂不支持文件格式: {filename}。当前仅支持 PDF 格式。")
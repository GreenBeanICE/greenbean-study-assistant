# PDF 解析器占位文件，后续用于解析 PDF 文本、页码和结构信息。
# backend-python/app/app/parsers/pdf_parser.py
import fitz  # PyMuPDF
from typing import List, Dict, Any

class PDFParser:
    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        解析 PDF 字节流，提取文本并构建初始的 PageIndex 结构。
        
        :param file_content: 前端上传文件的二进制数据
        :return: 包含每页文本和元数据的列表
        """
        # 从内存中的字节流直接打开 PDF，避免本地磁盘二次 I/O
        doc = fitz.open(stream=file_content, filetype="pdf")
        parsed_pages = []
        
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # 提取纯文本
                text = page.get_text("text").strip()
                
                # 构造单页的 PageIndex 节点
                page_node = {
                    "page_number": page_num + 1,
                    "content": text,
                    "char_count": len(text),
                    "parser_name": "PDFParser",
                    "parser_version": "1.0.0",
                    "metadata": {
                        "source_type": "pdf",
                        "headings": [],
                        "paragraphs_count": 0,
                    }
                }
                parsed_pages.append(page_node)
        finally:
            doc.close()
            
        return parsed_pages
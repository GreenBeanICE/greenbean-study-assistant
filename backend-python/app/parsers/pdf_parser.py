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
                        "paragraphs_count": len([p for p in text.split("\n\n") if p.strip()]),
                    }
                }
                parsed_pages.append(page_node)
        finally:
            doc.close()
            
        return parsed_pages

    def extract_outline(self, file_content: bytes) -> List[Dict[str, Any]]:
        """读取 PDF 自带 outline/bookmarks，并映射为候选章节节点。"""
        doc = fitz.open(stream=file_content, filetype="pdf")
        try:
            toc = doc.get_toc(simple=True)
            if not toc:
                return []

            items: list[dict[str, Any]] = []
            parent_stack: list[tuple[int, str]] = []
            for index, (level, title, page_number) in enumerate(toc):
                temp_id = f"pdf-outline-{index + 1}"
                while parent_stack and parent_stack[-1][0] >= level:
                    parent_stack.pop()
                parent_temp_id = parent_stack[-1][1] if parent_stack else None
                items.append(
                    {
                        "temp_id": temp_id,
                        "title": title.strip() or f"Section {index + 1}",
                        "level": int(level),
                        "parent_temp_id": parent_temp_id,
                        "start_page": max(1, int(page_number)),
                        "end_page": len(doc),
                        "order_index": index,
                    }
                )
                parent_stack.append((int(level), temp_id))

            for index, item in enumerate(items):
                next_item = next(
                    (
                        candidate
                        for candidate in items[index + 1 :]
                        if candidate["level"] <= item["level"]
                    ),
                    None,
                )
                if next_item is not None:
                    item["end_page"] = max(
                        item["start_page"],
                        next_item["start_page"] - 1,
                    )
            return items
        finally:
            doc.close()

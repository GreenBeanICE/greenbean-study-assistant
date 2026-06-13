"""
Word 文档解析器，用于解析 .docx 文件，提取文本、表格和标题层级。
输出统一的 PageIndex 结构，与 PDFParser 保持一致。
"""
import io
from typing import List, Dict, Any
from docx import Document
from app.utils.text_utils import clean_text


class WordParser:
    """解析 .docx 格式的 Word 文档，提取结构化文本内容。"""

    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        解析 Word 文档字节流，提取文本并构建 PageIndex 结构。
        
        Word 文档没有"页"的概念，整体视为 1 个 PageIndex 节点。
        
        :param file_content: 前端上传文件的二进制数据
        :return: 包含文本和元数据的列表（单元素列表）
        """
        # 使用 BytesIO 包装字节流，因为 python-docx 的 Document 不支持直接传 stream 参数
        doc = Document(io.BytesIO(file_content))
        
        # 提取所有段落文本
        paragraphs_text = []
        headings = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            paragraphs_text.append(text)
            # 识别标题样式
            if para.style and para.style.name and para.style.name.startswith("Heading"):
                headings.append({
                    "level": int(para.style.name.replace("Heading ", "0") or "0"),
                    "text": text
                })
        
        # 提取所有表格文本
        tables_text = []
        for table in doc.tables:
            table_content = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                table_content.append(" | ".join(row_cells))
            tables_text.append("\n".join(table_content))
        
        # 合并所有文本
        all_parts = []
        if paragraphs_text:
            all_parts.append("\n\n".join(paragraphs_text))
        if tables_text:
            all_parts.append("\n\n--- 表格内容 ---\n" + "\n\n".join(tables_text))
        
        full_text = "\n\n".join(all_parts)
        full_text = clean_text(full_text)
        
        # 构造单页的 PageIndex 节点
        page_node = {
            "page_number": 1,
            "content": full_text,
            "char_count": len(full_text),
            "parser_name": "WordParser",
            "parser_version": "1.0.0",
            "metadata": {
                "source_type": "word",
                "paragraphs_count": len(paragraphs_text),
                "tables_count": len(tables_text),
                "headings": headings,
            }
        }
        
        return [page_node]

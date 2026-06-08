"""
纯文本解析器，用于解析 .txt 和 .md 格式文件。
输出统一的 PageIndex 结构，与 PDFParser 保持一致。
"""
from typing import List, Dict, Any
from app.utils.text_utils import clean_text


class TextParser:
    """解析 .txt / .md 格式的纯文本文件。"""

    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        解析文本字节流，提取内容并构建 PageIndex 结构。
        
        纯文本文件整体视为 1 个 PageIndex 节点。
        
        :param file_content: 前端上传文件的二进制数据
        :return: 包含文本和元数据的列表（单元素列表）
        """
        # 解码字节流为文本
        try:
            text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            # 如果 UTF-8 解码失败，尝试 GBK（常见于中文 Windows 环境）
            try:
                text = file_content.decode("gbk")
            except UnicodeDecodeError:
                # 最后尝试 latin-1（不会失败，但可能乱码）
                text = file_content.decode("latin-1")
        
        text = clean_text(text)
        
        # 统计段落数（按空行分割）
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        
        # 检测是否为 Markdown（简单判断是否包含 md 语法）
        is_markdown = any(text.startswith(c) for c in ["# ", "## ", "### ", "---", "```"])
        
        # 提取 Markdown 标题
        headings = []
        if is_markdown:
            for line in text.split("\n"):
                stripped = line.strip()
                if stripped.startswith("#"):
                    level = len(stripped) - len(stripped.lstrip("#"))
                    heading_text = stripped.lstrip("#").strip()
                    if heading_text:
                        headings.append({"level": level, "text": heading_text})
        
        page_node = {
            "page_number": 1,
            "content": text,
            "char_count": len(text),
            "metadata": {
                "source_type": "text",
                "is_markdown": is_markdown,
                "paragraphs_count": len(paragraphs),
                "headings": headings,
            }
        }
        
        return [page_node]

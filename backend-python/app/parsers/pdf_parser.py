# PDF 解析器，支持结构化 blocks 和标题候选抽取。
# backend-python/app/parsers/pdf_parser.py
import re
import fitz  # PyMuPDF
from typing import List, Dict, Any

# 标题识别相关常量
TOP_REGION_RATIO = 0.3
BOTTOM_REGION_RATIO = 0.7
SHORT_TEXT_THRESHOLD = 80
MEDIUM_TEXT_THRESHOLD = 150
FONT_SIZE_RATIO_STRONG = 1.5
FONT_SIZE_RATIO_MEDIUM = 1.2
HEADING_CONFIDENCE_THRESHOLD = 0.4
DECIMAL_HEADING_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)(?:\.(?=\s)|(?=\s)|$)")
HEADING_TEXT_START_PATTERN = re.compile(r"^[A-Z\u00C0-\u024F\u4e00-\u9fff]")


class PDFParser:
    def _extract_decimal_heading_token(self, text: str) -> tuple[str, int] | None:
        """提取十进制标题编号，并推导层级。"""
        stripped_text = text.strip()
        match = DECIMAL_HEADING_PATTERN.match(stripped_text)
        if not match:
            return None

        token = match.group(1)
        remaining_text = stripped_text[match.end():].strip()

        if remaining_text and not HEADING_TEXT_START_PATTERN.match(remaining_text):
            return None

        numbering_level = len(token.split("."))
        return token, numbering_level

    def _extract_blocks(self, page) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """从 PyMuPDF page 提取结构化 blocks 和 page_stats。"""
        blocks = []
        text_dict = page.get_text("dict")

        # 收集所有字号用于统计
        font_sizes = []
        block_id = 0

        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # 只处理文本块
                continue

            block_text = ""
            block_font_size = 0.0
            block_font_name = ""
            block_is_bold = False

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span.get("text", "").strip()
                    if span_text:
                        block_text += span_text + " "
                        block_font_size = span.get("size", 0.0)
                        block_font_name = span.get("font", "")
                        font_sizes.append(block_font_size)
                        if "Bold" in block_font_name or "bold" in block_font_name.lower():
                            block_is_bold = True

            block_text = block_text.strip()
            if not block_text:
                continue

            bbox = block.get("bbox", (0, 0, 0, 0))
            blocks.append({
                "id": f"b-{block_id}",
                "text": block_text,
                "bbox": list(bbox),
                "font_size": block_font_size,
                "font_name": block_font_name,
                "is_bold": block_is_bold,
                "line_count": len(block.get("lines", [])),
                "is_top_region": bbox[1] < page.rect.height * TOP_REGION_RATIO,
                "is_bottom_region": bbox[3] > page.rect.height * BOTTOM_REGION_RATIO,
                "sequence_index": block_id,
            })
            block_id += 1

        # 计算 page_stats
        primary_font_size = max(set(font_sizes), key=font_sizes.count) if font_sizes else 10.0
        max_font_size = max(font_sizes) if font_sizes else 10.0

        page_stats = {
            "page_width": page.rect.width,
            "page_height": page.rect.height,
            "primary_font_size": primary_font_size,
            "max_font_size": max_font_size,
            "top_margin_cutoff": page.rect.height * 0.1,
            "bottom_margin_cutoff": page.rect.height * 0.9,
        }

        return blocks, page_stats

    def _detect_heading_candidates(self, blocks: list[dict[str, Any]], page_stats: dict[str, Any]) -> list[dict[str, Any]]:
        """从 blocks 中识别标题候选。"""
        headings = []
        primary_font_size = page_stats["primary_font_size"]

        fallback_patterns = [
            (r"^Chapter\s+(\d+)", "chapter", 1),
            (r"^Section\s+(\d+)", "section", 1),
            (r"^第(\d+)章", "chapter_zh", 1),
            (r"^第(\d+)节", "section_zh", 2),
            (r"^([一二三四五六七八九十]+)、", "chinese", 1),
            (r"^（([一二三四五六七八九十]+)）", "chinese_paren", 2),
        ]

        for block in blocks:
            text = block["text"].strip()
            if not text:
                continue

            confidence = 0.0
            heading_level = 1
            pattern_name = ""

            # 视觉信号：字号明显大于主字号
            font_size_ratio = block["font_size"] / primary_font_size if primary_font_size > 0 else 1.0
            if font_size_ratio >= FONT_SIZE_RATIO_STRONG:
                confidence += 0.4
            elif font_size_ratio >= FONT_SIZE_RATIO_MEDIUM:
                confidence += 0.2

            # 视觉信号：粗体
            if block["is_bold"]:
                confidence += 0.2

            # 文本信号：优先识别十进制编号，再回退到其他编号规则。
            decimal_match = self._extract_decimal_heading_token(text)
            if decimal_match is not None:
                _, numbering_level = decimal_match
                confidence += 0.3
                heading_level = numbering_level
                pattern_name = "decimal"
            else:
                for pattern, name, default_level in fallback_patterns:
                    if re.match(pattern, text):
                        confidence += 0.3
                        heading_level = default_level
                        pattern_name = name
                        break

            # 文本信号：短文本（标题通常较短）
            if len(text) < SHORT_TEXT_THRESHOLD:
                confidence += 0.1
            elif len(text) < MEDIUM_TEXT_THRESHOLD:
                confidence += 0.05

            # 位置信号：上半区
            if block["is_top_region"]:
                confidence += 0.1

            # 只有置信度足够高才进入 headings
            if confidence >= HEADING_CONFIDENCE_THRESHOLD:
                headings.append({
                    "title": text,
                    "level": heading_level,
                    "confidence": min(confidence, 1.0),
                    "source_block_id": block["id"],
                    "numbering_pattern": pattern_name,
                })

        return headings

    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        解析 PDF 字节流，提取文本并构建结构化 PageIndex。

        :param file_content: 前端上传文件的二进制数据
        :return: 包含每页文本、结构化 blocks 和标题候选的列表
        """
        doc = fitz.open(stream=file_content, filetype="pdf")
        parsed_pages = []

        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # 提取结构化 blocks
                blocks, page_stats = self._extract_blocks(page)

                # 提取纯文本用于兼容
                text = page.get_text("text").strip()

                # 检测标题候选
                headings = self._detect_heading_candidates(blocks, page_stats)

                # 构造 page node
                page_node = {
                    "page_number": page_num + 1,
                    "content": text,
                    "char_count": len(text),
                    "parser_name": "PDFParser",
                    "parser_version": "2.0.0",
                    "metadata": {
                        "source_type": "pdf",
                        "headings": headings,
                        "paragraphs_count": len([p for p in text.split("\n\n") if p.strip()]),
                        "page_stats": page_stats,
                    },
                    "blocks": blocks,
                }
                parsed_pages.append(page_node)
        finally:
            doc.close()

        return parsed_pages

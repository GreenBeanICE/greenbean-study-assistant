"""
PPT 解析器，用于解析 .pptx 格式文件，提取文本、标题和备注。
基于 python-pptx 库实现。

输出统一的 PageIndex 结构，与 PDFParser 保持一致。
"""
import io
from typing import List, Dict, Any
from pptx import Presentation
from app.utils.text_utils import clean_text


class PptParser:
    """解析 .pptx 格式的 PowerPoint 文件，提取结构化文本内容。"""

    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        解析 PPT 字节流，逐页提取文本并构建 PageIndex 结构。
        
        每张幻灯片视为 1 个 PageIndex 节点。
        
        :param file_content: 前端上传文件的二进制数据
        :return: 包含每页文本和元数据的列表
        """
        prs = Presentation(io.BytesIO(file_content))
        parsed_pages = []
        
        for slide_num, slide in enumerate(prs.slides, start=1):
            slide_texts = []
            headings = []
            
            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                
                for paragraph in shape.text_frame.paragraphs:
                    text = paragraph.text.strip()
                    if not text:
                        continue
                    slide_texts.append(text)
                    
                    # 检测是否为标题（基于字体大小或占位符类型）
                    is_title = False
                    if shape.is_placeholder:
                        ph = shape.placeholder_format
                        if ph.idx == 0:  # 标题占位符通常 idx=0
                            is_title = True
                    
                    if is_title:
                        headings.append({
                            "level": 1,
                            "text": text
                        })
            
            full_text = "\n".join(slide_texts)
            full_text = clean_text(full_text)
            
            page_node = {
                "page_number": slide_num,
                "content": full_text,
                "char_count": len(full_text),
                "metadata": {
                    "source_type": "ppt",
                    "headings": headings,
                    "shapes_count": len(slide.shapes),
                    "paragraphs_count": len(slide_texts),
                }
            }
            parsed_pages.append(page_node)
        
        return parsed_pages

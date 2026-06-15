"""
文件工具模块，用于封装路径、扩展名和文件类型检测辅助逻辑。
"""
import os
from typing import Set

# ---- 文件扩展名字面量常量 ----
EXT_PDF = ".pdf"
EXT_DOCX = ".docx"
EXT_PPTX = ".pptx"
EXT_JPG = ".jpg"
EXT_JPEG = ".jpeg"
EXT_PNG = ".png"
EXT_WEBP = ".webp"
EXT_TXT = ".txt"
EXT_MD = ".md"

# 定义支持的文件扩展名集合
SUPPORTED_EXTENSIONS: Set[str] = {
    EXT_PDF, EXT_DOCX,
    EXT_PPTX,
    EXT_JPG, EXT_JPEG, EXT_PNG, EXT_WEBP,
    EXT_TXT, EXT_MD,
}

# 图片文件扩展名
IMAGE_EXTENSIONS: Set[str] = {EXT_JPG, EXT_JPEG, EXT_PNG, EXT_WEBP}

# 文档文件扩展名
DOCUMENT_EXTENSIONS: Set[str] = {EXT_PDF, EXT_DOCX, EXT_PPTX, EXT_TXT, EXT_MD}

# MIME 类型映射
_MIME_MAP: dict[str, str] = {
    EXT_PDF: "application/pdf",
    EXT_DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    EXT_PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    EXT_JPG: "image/jpeg",
    EXT_JPEG: "image/jpeg",
    EXT_PNG: "image/png",
    EXT_WEBP: "image/webp",
    EXT_TXT: "text/plain",
    EXT_MD: "text/markdown",
}


def get_extension(filename: str) -> str:
    """
    获取文件扩展名（小写）。
    
    :param filename: 文件名
    :return: 小写扩展名，例如 '.pdf', '.jpg'
    """
    return os.path.splitext(filename)[1].lower()


def is_supported(filename: str) -> bool:
    """
    检查文件扩展名是否受支持。
    
    :param filename: 文件名
    :return: True 如果扩展名受支持
    """
    ext = get_extension(filename)
    return ext in SUPPORTED_EXTENSIONS


def is_image(filename: str) -> bool:
    """
    检查是否为图片文件。
    
    :param filename: 文件名
    :return: True 如果是图片格式
    """
    ext = get_extension(filename)
    return ext in IMAGE_EXTENSIONS


def is_document(filename: str) -> bool:
    """
    检查是否为文档文件。
    
    :param filename: 文件名
    :return: True 如果是文档格式
    """
    ext = get_extension(filename)
    return ext in DOCUMENT_EXTENSIONS


def get_mime_type(filename: str) -> str:
    """
    根据扩展名返回 MIME 类型。
    
    :param filename: 文件名
    :return: MIME 类型字符串
    """
    ext = get_extension(filename)
    return _MIME_MAP.get(ext, "application/octet-stream")

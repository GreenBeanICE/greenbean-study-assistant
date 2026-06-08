"""
文件工具模块，用于封装路径、扩展名和文件类型检测辅助逻辑。
"""
import os
from typing import Set

# 定义支持的文件扩展名集合
SUPPORTED_EXTENSIONS: Set[str] = {
    ".pdf", ".docx", ".doc",
    ".pptx",
    ".jpg", ".jpeg", ".png", ".webp",
    ".txt", ".md",
}

# 图片文件扩展名
IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp"}

# 文档文件扩展名
DOCUMENT_EXTENSIONS: Set[str] = {".pdf", ".docx", ".doc", ".pptx", ".txt", ".md"}


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
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }
    ext = get_extension(filename)
    return mime_map.get(ext, "application/octet-stream")

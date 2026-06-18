"""
文本工具模块，用于封装清洗、截断和格式化辅助逻辑。
"""
import re
from typing import List, Optional


def clean_text(text: str) -> str:
    """
    清洗文本：去除多余空白、空行，规范化换行符。
    
    :param text: 原始文本
    :return: 清洗后的文本
    """
    if not text:
        return ""
    
    # 统一换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # 去除连续空白行（保留单个换行）
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # 去除首尾空白
    text = text.strip()
    
    return text


def truncate_text(text: str, max_chars: int = 10000, ellipsis: str = "...") -> str:
    """
    截断文本到指定最大字符数。
    
    :param text: 原始文本
    :param max_chars: 最大字符数
    :param ellipsis: 截断后缀
    :return: 截断后的文本
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + ellipsis


def split_into_paragraphs(text: str) -> List[str]:
    """
    将文本按空行分割为段落列表。
    
    :param text: 原始文本
    :return: 段落列表
    """
    if not text:
        return []
    
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


def count_words(text: str) -> int:
    """
    统计文本中的单词数（适用于英文、法文等空格分隔的语言）。
    
    :param text: 文本
    :return: 单词数
    """
    if not text:
        return 0
    return len(text.split())


def contains_chinese(text: str) -> bool:
    """
    检测文本是否包含中文字符。
    
    :param text: 文本
    :return: True 如果包含中文字符
    """
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def contains_french(text: str) -> bool:
    """
    检测文本是否包含法语特殊字符。
    
    :param text: 文本
    :return: True 如果包含法语字符
    """
    return bool(re.search(r"[éèêëàâäùûüôöîïçœæ]", text, re.IGNORECASE))


def detect_language(text: str) -> str:
    """
    简单检测文本主要语言（中/英/法）。
    
    :param text: 文本
    :return: 语言代码 'zh', 'fr', 'en'
    """
    if not text:
        return "en"
    
    sample = text[:500]
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", sample))
    french_chars = len(re.findall(r"[éèêëàâäùûüôöîïçœæ]", sample, re.IGNORECASE))
    
    if chinese_chars > len(sample) * 0.1:
        return "zh"
    elif french_chars > 3:
        return "fr"
    else:
        return "en"

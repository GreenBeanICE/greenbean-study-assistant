# AnalysisType 枚举占位文件，后续用于描述分析类型。
from enum import Enum


class AnalysisType(str, Enum):
    FULL_DOCUMENT = "full_document"
    SECTION = "section"

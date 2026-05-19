# AnalysisType 枚举占位文件，后续用于描述分析类型。
from enum import Enum

class AnalysisType(str, Enum):
    """
    定义 Agent 可能的路由分发类型。
    """
    STRUCTURE = "STRUCTURE"         # 涉及文档大纲或具体的页码
    CONCEPT = "CONCEPT"             # 涉及特定概念的定义与解释（RAG检索）
    COMPREHENSIVE = "COMPREHENSIVE" # 结合前两者的综合问题，或无法确定的默认情况
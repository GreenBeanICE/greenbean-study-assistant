# 分析请求和响应 Schema 占位文件，后续用于定义 Pydantic 数据结构。
from pydantic import BaseModel, Field
from app.enums.analysis_type import AnalysisType

class RoutingDecision(BaseModel):
    """
    用于验证 Agent 结构化输出的数据模型。
    """
    route: AnalysisType = Field(
        description="为当前问题选择的路由分类"
    )
    reason: str = Field(
        description="用简短的语言解释选择该路由分类的理由"
    )
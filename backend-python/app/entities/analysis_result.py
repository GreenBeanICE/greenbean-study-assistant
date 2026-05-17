from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.enums.analysis_type import AnalysisType


class AnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="分析结果唯一 ID，使用 UUID 字符串。")
    document_id: str = Field(..., description="被分析的文档 ID。")
    section_id: str | None = Field(default=None, description="被分析的小节 ID；全文解析时为空。")
    analysis_type: AnalysisType = Field(..., description="分析类型，区分全文解析和小节解析。")
    language: str = Field(..., description="分析结果语言。")
    content_markdown: str = Field(..., description="用于展示的 Markdown 内容。")
    content_json: dict[str, Any] | None = Field(default=None, description="用于程序读取的结构化分析内容。")
    model_name: str | None = Field(default=None, description="生成结果的 AI 模型名称。")
    prompt_version: str | None = Field(default=None, description="生成结果时使用的提示词模板版本。")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间。")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="最后更新时间。")

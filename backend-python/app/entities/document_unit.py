from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class DocumentUnit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="内容单元唯一 ID。")
    document_id: str = Field(..., description="所属文档 ID。")
    sequence_index: int = Field(
        ...,
        description="同一文档内的内容单元顺序；持久化层应保证同一文档内唯一。",
    )
    text_content: str = Field(..., description="统一正文内容，用于展示、检索和 AI 分析。")
    page_number: int | None = Field(default=None, description="来源页码。")
    start_char: int | None = Field(default=None, description="在原始文本流中的起始字符位置。")
    end_char: int | None = Field(default=None, description="在原始文本流中的结束字符位置。")
    token_count: int | None = Field(default=None, description="内容单元的 token 数。")
    metadata_json: dict[str, Any] | None = Field(default=None, description="用于检索、过滤和展示的元数据。")
    raw_content_json: dict[str, Any] | None = Field(default=None, description="解析器输出的原始布局或 OCR 信息。")
    parser_name: str | None = Field(default=None, description="生成该内容单元的解析器或切分器名称。")
    parser_version: str | None = Field(default=None, description="生成该内容单元的解析器或切分器版本。")
    external_id: str | None = Field(default=None, description="外部解析器生成的原始 ID。")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间。")

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Section(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="小节唯一 ID，使用 UUID 字符串。")
    document_id: str = Field(..., description="所属文档 ID。")
    parent_section_id: str | None = Field(default=None, description="父级小节 ID。")
    title: str = Field(..., description="小节标题。")
    level: int = Field(..., description="小节层级，数值越小层级越高。")
    order_index: int = Field(..., description="小节在同级结构中的顺序。")
    start_page: int | None = Field(default=None, description="小节起始页码。")
    end_page: int | None = Field(default=None, description="小节结束页码。")
    summary: str | None = Field(default=None, description="小节摘要。")
    metadata_json: dict[str, Any] | None = Field(default=None, description="结构索引用于展示或过滤的元数据。")
    parser_name: str | None = Field(default=None, description="生成该结构节点的解析器名称。")
    parser_version: str | None = Field(default=None, description="生成该结构节点的解析器版本。")
    external_id: str | None = Field(default=None, description="外部结构解析器生成的原始 ID。")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间。")

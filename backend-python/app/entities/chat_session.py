from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="会话唯一 ID，使用 UUID 字符串。")
    workspace_id: str = Field(..., description="所属工作区 ID。")
    document_id: str | None = Field(default=None, description="关联文档 ID；工作区级会话时为空。")
    title: str = Field(..., description="会话标题。")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间。")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="最后更新时间。")

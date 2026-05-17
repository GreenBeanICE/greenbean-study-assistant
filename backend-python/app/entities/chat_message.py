from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.enums.message_role import MessageRole


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="消息唯一 ID，使用 UUID 字符串。")
    session_id: str = Field(..., description="所属会话 ID。")
    role: MessageRole = Field(..., description="消息角色。")
    content: str = Field(..., description="消息正文。")
    source_context_json: dict[str, Any] | None = Field(default=None, description="回答引用的检索上下文。")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间。")

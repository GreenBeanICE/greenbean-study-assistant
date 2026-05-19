from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class Workspace(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="工作区唯一 ID，使用 UUID 字符串。")
    name: str = Field(..., description="工作区名称。")
    description: str | None = Field(default=None, description="工作区说明。")
    type: str | None = Field(default=None, description="工作区类型，可使用默认值或用户自定义值。")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间。")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="最后更新时间。")

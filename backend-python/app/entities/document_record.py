from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from app.enums.document_file_type import DocumentFileType
from app.enums.document_status import DocumentStatus


class DocumentRecord(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="文档记录唯一 ID，使用 UUID 字符串。",
    )
    workspace_id: str = Field(..., description="所属工作区 ID。")
    title: str = Field(..., description="文档显示标题。")
    original_filename: str = Field(..., description="用户上传时的原始文件名。")
    file_type: DocumentFileType = Field(..., description="文档文件类型。")
    file_path: str = Field(..., description="原始文件在本地 uploads 目录下的路径。")
    file_hash: str | None = Field(default=None, description="原始文件哈希值。")
    status: DocumentStatus = Field(
        default=DocumentStatus.UPLOADED, description="文档处理状态。"
    )
    page_count: int | None = Field(default=None, description="文档页数。")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="创建时间。"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="最后更新时间。"
    )

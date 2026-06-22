"""文档 API 请求和响应 Schema。

定义上传响应、列表项、详情响应等 Pydantic 结构，
不把 entity 原样暴露给前端。
"""
from datetime import datetime

from pydantic import BaseModel

from app.entities import DocumentRecord, DocumentUnit
from app.enums.document_file_type import DocumentFileType
from app.enums.document_status import DocumentStatus


def _document_common_fields(doc: DocumentRecord) -> dict:
    """提取文档通用字段，供多个 schema 复用。"""
    return {
        "id": doc.id,
        "title": doc.title,
        "original_filename": doc.original_filename,
        "file_type": doc.file_type,
        "status": doc.status,
        "page_count": doc.page_count,
        "created_at": doc.created_at,
    }


class DocumentUploadResponse(BaseModel):
    id: str
    title: str
    original_filename: str
    file_type: DocumentFileType
    status: DocumentStatus
    page_count: int | None
    created_at: datetime

    @classmethod
    def from_entity(cls, doc: DocumentRecord) -> "DocumentUploadResponse":
        return cls(**_document_common_fields(doc))


class DocumentListItem(BaseModel):
    id: str
    workspace_id: str
    title: str
    original_filename: str
    file_type: DocumentFileType
    status: DocumentStatus
    page_count: int | None
    created_at: datetime

    @classmethod
    def from_entity(cls, doc: DocumentRecord) -> "DocumentListItem":
        return cls(workspace_id=doc.workspace_id, **_document_common_fields(doc))


class DocumentUnitSummary(BaseModel):
    id: str
    sequence_index: int
    page_number: int | None
    text_content: str

    @classmethod
    def from_entity(cls, unit: DocumentUnit) -> "DocumentUnitSummary":
        return cls(
            id=unit.id,
            sequence_index=unit.sequence_index,
            page_number=unit.page_number,
            text_content=unit.text_content,
        )


class DocumentDetailResponse(BaseModel):
    document: DocumentListItem
    units: list[DocumentUnitSummary]

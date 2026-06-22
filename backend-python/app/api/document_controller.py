"""
文档接口控制器，提供文档上传、列表和详情相关 API。
"""
import hashlib
from typing import Annotated

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi import status as http_status

from app.api.dependencies import get_document_query_service, get_ingest_service
from app.schemas.document_schema import (
    DocumentDetailResponse,
    DocumentListItem,
    DocumentUploadResponse,
    DocumentUnitSummary,
)
from app.services.document_ingest_service import DocumentIngestService
from app.services.document_query_service import DocumentQueryService
from app.utils.file_utils import is_supported, get_extension

router = APIRouter(prefix="/documents", tags=["Documents"])

# ---- 错误响应定义（供 @router 装饰器复用） ----
_RESPONSE_400_BAD_REQUEST = {
    http_status.HTTP_400_BAD_REQUEST: {"description": "请求参数无效"}
}
_RESPONSE_500_INTERNAL_ERROR = {
    http_status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "服务器内部错误"}
}
_RESPONSE_400_AND_500 = {**_RESPONSE_400_BAD_REQUEST, **_RESPONSE_500_INTERNAL_ERROR}

# 支持的格式描述信息，供错误提示复用
_SUPPORTED_FORMATS_MSG = (
    "PDF(.pdf), Word(.docx), PPT(.pptx), 纯文本(.txt/.md), 图片(.jpg/.jpeg/.png/.webp)"
)
_DEFAULT_WORKSPACE_ID = "workspace_1"


@router.post(
    "/upload",
    responses=_RESPONSE_400_AND_500,
)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    ingest_service: Annotated[DocumentIngestService, Depends(get_ingest_service)],
    workspace_id: Annotated[str, Form()] = _DEFAULT_WORKSPACE_ID,
):
    """
    接收前端通过 FormData 传来的文件，调用 Service 流水线进行解析与导入。

    支持的文件格式:
    - 文档: PDF(.pdf), Word(.docx), PPT(.pptx), 纯文本(.txt/.md)
    - 图片: JPG/JPEG, PNG, WEBP
    """
    # 检查文件名是否存在
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 检查文件格式是否支持
    if not is_supported(file.filename):
        ext = get_extension(file.filename)
        raise HTTPException(
            status_code=400,
            detail=f"暂不支持 {ext} 格式。支持的格式: {_SUPPORTED_FORMATS_MSG}",
        )

    try:
        # 读取文件二进制流
        file_content = await file.read()

        # 检查文件是否为空
        if not file_content:
            raise HTTPException(status_code=400, detail="文件内容为空")

        # 进入导入流水线
        file_hash = hashlib.sha256(file_content).hexdigest()
        result = ingest_service.ingest_document(
            file.filename,
            file_content,
            workspace_id=workspace_id,
            file_hash=file_hash,
        )
        upload_response = DocumentUploadResponse.from_entity(result["document_record"])

        return {
            "code": 200,
            "message": "文件上传并解析成功",
            "data": upload_response,
        }

    except ValueError as ve:
        # 捕获类似"不支持的文件格式"等业务异常
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        # 重新抛出已处理的 HTTP 异常
        raise
    except Exception as e:
        # 捕获系统底层或未知异常
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


@router.get("")
def list_documents(
    query_service: Annotated[DocumentQueryService, Depends(get_document_query_service)],
    workspace_id: str = _DEFAULT_WORKSPACE_ID,
):
    """按 workspace 返回文档列表，不暴露 file_path。"""
    documents = query_service.list_by_workspace(workspace_id)
    items = [DocumentListItem.from_entity(doc) for doc in documents]
    return {"code": 200, "data": items}


@router.get("/{document_id}")
def get_document_detail(
    document_id: str,
    query_service: Annotated[DocumentQueryService, Depends(get_document_query_service)],
):
    """返回文档详情，包含 document 和 units。不存在时返回 404。"""
    detail = query_service.get_document_detail(document_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    return {
        "code": 200,
        "data": DocumentDetailResponse(
            document=DocumentListItem.from_entity(detail["document"]),
            units=[DocumentUnitSummary.from_entity(unit) for unit in detail["units"]],
        ),
    }

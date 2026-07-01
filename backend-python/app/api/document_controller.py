"""
文档接口控制器，提供文档上传、列表和详情相关 API。
"""
from typing import Annotated, Any

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.db.connection import get_db_session
from app.entities import DocumentRecord, Section
from app.providers.embedding_registry import (
    EmbeddingProviderNotFoundError,
    EmbeddingProviderRegistry,
)
from app.providers.registry import ProviderNotFoundError, ProviderRegistry
from app.rag.vector_index_builder import SQLiteVecIndexBuilder
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.section_repository import SectionRepository
from app.services.document_ingest_service import DocumentIngestService
from app.services.embedding_service import EmbeddingService
from app.services.section_service import (
    OutlineCandidateService,
    OutlineConfirmationService,
)
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


def get_ingest_service(
    session: Session | None = Depends(get_db_session),
) -> DocumentIngestService:
    """依赖注入：确保每个请求能正确拿到 IngestService 实例。"""
    if not isinstance(session, Session):
        return DocumentIngestService()
    return DocumentIngestService(
        document_repository=DocumentRepository(session),
        document_unit_repository=DocumentUnitRepository(session),
    )


@router.post(
    "/upload",
    responses=_RESPONSE_400_AND_500,
)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    ingest_service: Annotated[DocumentIngestService, Depends(get_ingest_service)],
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
        result = ingest_service.ingest_document(file.filename, file_content)
        if "page_index" not in result:
            return {
                "code": 200,
                "message": "文件上传并解析成功",
                "data": result,
            }
        outline_service = OutlineCandidateService()
        page_index = result["page_index"]
        candidates = outline_service.build_candidates(
            document_id=result["document_id"],
            page_index=page_index,
            pdf_outline=result["pdf_outline"],
            chat_provider=None,
        )
        try:
            chat_provider = ProviderRegistry.get_active()
            candidates["outline_candidates"][1] = await outline_service.build_llm_candidate(
                document_id=result["document_id"],
                page_index=page_index,
                chat_provider=chat_provider,
            )
        except ProviderNotFoundError:
            pass
        ingest_service.commit()
        
        return {
            "code": 200,
            "message": "文件上传并解析成功",
            "data": _upload_result_to_response(result, candidates),
        }
        
    except ValueError as ve:
        ingest_service.rollback()
        # 捕获类似"不支持的文件格式"等业务异常
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        ingest_service.rollback()
        # 重新抛出已处理的 HTTP 异常
        raise
    except Exception as e:
        ingest_service.rollback()
        # 捕获系统底层或未知异常
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


@router.post("/{document_id}/outline/confirm")
async def confirm_outline(
    document_id: str,
    request: dict[str, Any],
    session: Annotated[Session, Depends(get_db_session)],
):
    document = DocumentRepository(session).get_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
    candidate = request.get("candidate")
    if not isinstance(candidate, dict):
        raise HTTPException(status_code=400, detail="candidate is required")

    embedding_dimension = 768
    service = OutlineConfirmationService(
        section_repository=SectionRepository(session),
        document_unit_repository=DocumentUnitRepository(session),
        chunk_repository=ChunkRepository(session),
        embedding_repository=EmbeddingRepository(
            session,
            embedding_dimension=embedding_dimension,
        ),
        vector_index_builder=SQLiteVecIndexBuilder(
            session=session,
            embedding_dimension=embedding_dimension,
        ),
        chunk_size=1200,
    )
    try:
        result = service.confirm(document=document, candidate=candidate)
        result["embedding_status"] = await _try_embed_and_index_chunks(
            session=session,
            chunks=result["chunks"],
        )
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"确认大纲失败: {exc}") from exc

    return {
        "code": 200,
        "message": "大纲确认完成",
        "data": {
            "sections": [_section_to_dict(section) for section in result["sections"]],
            "section_unit_links_status": result["section_unit_links_status"],
            "chunk_status": result["chunk_status"],
            "embedding_status": result["embedding_status"],
        },
    }


def _upload_result_to_response(
    result: dict[str, Any],
    candidates: dict[str, Any],
) -> dict[str, Any]:
    return {
        "document_id": result["document_id"],
        "filename": result["filename"],
        "page_count": result["page_count"],
        "total_pages": result["total_pages"],
        "status": result.get("processing_status", result["status"]),
        "page_index": candidates["page_index"],
        "page_index_preview": result["page_index_preview"],
        "outline_candidates": candidates["outline_candidates"],
        "document_record": _document_to_dict(result["document_record"]),
        "document_units": [
            {
                "id": unit.id,
                "document_id": unit.document_id,
                "sequence_index": unit.sequence_index,
                "page_number": unit.page_number,
                "text_content": unit.text_content,
                "start_char": unit.start_char,
                "end_char": unit.end_char,
                "metadata_json": unit.metadata_json,
                "parser_name": unit.parser_name,
                "parser_version": unit.parser_version,
            }
            for unit in result["document_units"]
        ],
    }


def _document_to_dict(document: DocumentRecord) -> dict[str, Any]:
    return {
        "id": document.id,
        "workspace_id": document.workspace_id,
        "title": document.title,
        "original_filename": document.original_filename,
        "file_type": document.file_type.value,
        "file_path": document.file_path,
        "file_hash": document.file_hash,
        "status": document.status.value,
        "page_count": document.page_count,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
    }


def _section_to_dict(section: Section) -> dict[str, Any]:
    return {
        "id": section.id,
        "document_id": section.document_id,
        "parent_section_id": section.parent_section_id,
        "title": section.title,
        "level": section.level,
        "order_index": section.order_index,
        "start_page": section.start_page,
        "end_page": section.end_page,
        "metadata_json": section.metadata_json,
    }


async def _try_embed_and_index_chunks(*, session: Session, chunks: list) -> str:
    if not chunks:
        return "empty"
    try:
        provider = EmbeddingProviderRegistry.get_active()
    except EmbeddingProviderNotFoundError:
        return "unavailable"

    embedding_dimension = provider.get_model_info().dimension
    embedding_service = EmbeddingService(
        EmbeddingRepository(session, embedding_dimension=embedding_dimension),
        provider=provider,
    )
    embeddings = await embedding_service.embed_chunks(chunks)
    vector_index = SQLiteVecIndexBuilder(
        session=session,
        embedding_dimension=embedding_dimension,
    )
    for embedding in embeddings:
        vector_index.upsert_chunk_embedding(
            chunk_id=embedding.chunk_id,
            vector=embedding.vector,
            embedding_model=embedding.embedding_model,
        )
    return "indexed"

# 分析接口控制器，提供小节解析相关 API。

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.db.connection import get_db_session
from app.entities.analysis_result import AnalysisResult
from app.providers.base import ProviderConfigurationError
from app.providers.embedding_registry import (
    EmbeddingProviderNotFoundError,
    EmbeddingProviderRegistry,
)
from app.providers.registry import ProviderNotFoundError
from app.rag.context_builder import (
    SectionContextBuilder,
    SectionNotFoundError,
    SectionPageRangeMissingError,
)
from app.repositories.analysis_result_repository import AnalysisResultRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.section_repository import SectionRepository
from app.rag.retriever import Retriever, SQLiteVecRetriever
from app.services.agentic_search_service import AgenticSearchService
from app.services.analysis_service import SectionAnalysisService
from app.services.embedding_service import EmbeddingService


router = APIRouter(prefix="/analysis", tags=["Analysis"])


class SectionAnalysisRequest(BaseModel):
    language: str = Field(default="zh", description="分析输出语言。")
    model_name: str | None = Field(default=None, description="指定 LLM 模型名称。")
    prompt_version: str = Field(
        default="section-analysis-v1",
        description="小节解析提示词版本。",
    )


class AgenticSearchRequest(BaseModel):
    query: str | None = Field(default=None, description="用户问题。")
    section_id: str | None = Field(default=None, description="可选小节 ID。")
    language: str = Field(default="zh", description="输出语言。")
    model_name: str | None = Field(default=None, description="指定 LLM 模型名称。")
    prompt_version: str = Field(default="agentic-search-v1", description="提示词版本。")
    top_k: int = Field(default=5, gt=0, le=20, description="检索 chunk 数量。")

    @model_validator(mode="after")
    def validate_query_or_section_id(self) -> "AgenticSearchRequest":
        if not self.query and not self.section_id:
            raise ValueError("query or section_id is required")
        return self

def get_section_analysis_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SectionAnalysisService:
    return SectionAnalysisService(
        context_builder=SectionContextBuilder(
            section_repository=SectionRepository(session),
            document_unit_repository=DocumentUnitRepository(session),
        ),
        analysis_result_repository=AnalysisResultRepository(session),
    )


def get_agentic_search_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> AgenticSearchService:
    try:
        embedding_provider = EmbeddingProviderRegistry.get_active()
        embedding_dimension = embedding_provider.get_model_info().dimension
    except EmbeddingProviderNotFoundError:
        embedding_provider = None
        embedding_dimension = 768
    section_context_builder = SectionContextBuilder(
        section_repository=SectionRepository(session),
        document_unit_repository=DocumentUnitRepository(session),
    )
    return AgenticSearchService(
        embedding_service=EmbeddingService(
            EmbeddingRepository(session, embedding_dimension=embedding_dimension),
            provider=embedding_provider,
        ),
        retriever=Retriever(
            vector_index=SQLiteVecRetriever(
                session=session,
                embedding_dimension=embedding_dimension,
            )
        ),
        section_context_builder=section_context_builder,
    )


@router.post("/sections/{section_id}")
async def analyze_section(
    section_id: str,
    request: SectionAnalysisRequest,
    service: Annotated[SectionAnalysisService, Depends(get_section_analysis_service)],
):
    try:
        result = await service.analyze_section(
            section_id=section_id,
            language=request.language,
            model_name=request.model_name,
            prompt_version=request.prompt_version,
        )
    except SectionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SectionPageRangeMissingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (ProviderNotFoundError, ProviderConfigurationError) as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "AI_PROVIDER_NOT_CONFIGURED",
                "message": "尚未配置 AI 模型服务",
            },
        ) from exc
    except (EmbeddingProviderNotFoundError, ProviderNotFoundError, ProviderConfigurationError) as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "AI_PROVIDER_NOT_CONFIGURED",
                "message": "尚未配置 AI 模型服务",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "code": 200,
        "message": "小节分析完成",
        "data": _analysis_result_to_dict(result),
    }


def _analysis_result_to_dict(result: AnalysisResult) -> dict:
    return {
        "id": result.id,
        "document_id": result.document_id,
        "section_id": result.section_id,
        "analysis_type": result.analysis_type.value,
        "language": result.language,
        "content_markdown": result.content_markdown,
        "content_json": result.content_json,
        "model_name": result.model_name,
        "prompt_version": result.prompt_version,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
    }


@router.post("/search")
async def agentic_search(
    request: AgenticSearchRequest,
    service: Annotated[AgenticSearchService, Depends(get_agentic_search_service)],
):
    try:
        result = await service.answer(
            query=request.query,
            section_id=request.section_id,
            language=request.language,
            model_name=request.model_name,
            prompt_version=request.prompt_version,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "code": 200,
        "message": "检索回答完成",
        "data": result,
    }

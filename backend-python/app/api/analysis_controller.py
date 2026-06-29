from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_analysis_service
from app.schemas.analysis_schema import (
    SectionAnalysisGenerateRequest,
    SectionAnalysisResponse,
)
from app.services.analysis_service import AnalysisService, SectionAnalysisNotFoundError

router = APIRouter(prefix="/analyses", tags=["Analyses"])


def _is_section_not_found_error(exc: ValueError) -> bool:
    return str(exc).startswith("Section not found:")


@router.get("/sections/{section_id}")
def get_section_analysis(
    section_id: str,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
):
    try:
        result = service.get_section_analysis(section_id)
    except SectionAnalysisNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        if _is_section_not_found_error(exc):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise

    if result is None:
        return {"code": 200, "data": None}
    return {"code": 200, "data": SectionAnalysisResponse.from_entity(result)}


@router.post("/sections/{section_id}/generate")
async def generate_section_analysis(
    section_id: str,
    payload: SectionAnalysisGenerateRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
):
    try:
        result = await service.generate_section_analysis(
            section_id,
            language=payload.language,
            force_regenerate=payload.force_regenerate,
        )
    except SectionAnalysisNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        if _is_section_not_found_error(exc):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"code": 200, "data": SectionAnalysisResponse.from_entity(result)}

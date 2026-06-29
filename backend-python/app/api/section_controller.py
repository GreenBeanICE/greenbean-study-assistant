from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_section_service
from app.schemas.section_schema import SectionContentResponse, SectionContentUnit, SectionSummary, SectionTreeNodeResponse
from app.services.section_service import SectionService

router = APIRouter(prefix="/sections", tags=["Sections"])


@router.post("/documents/{document_id}/build")
def build_sections(
    document_id: str,
    service: Annotated[SectionService, Depends(get_section_service)],
):
    sections = service.build_sections(document_id)
    return {"code": 200, "data": [SectionSummary.from_entity(section) for section in sections]}


@router.get("/documents/{document_id}/tree")
def get_section_tree(
    document_id: str,
    service: Annotated[SectionService, Depends(get_section_service)],
):
    tree = service.get_section_tree(document_id)
    return {"code": 200, "data": [SectionTreeNodeResponse.from_node(node) for node in tree]}


@router.get("/{section_id}/content")
def get_section_content(
    section_id: str,
    service: Annotated[SectionService, Depends(get_section_service)],
):
    try:
        result = service.get_section_content(section_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "code": 200,
        "data": SectionContentResponse(
            anchor_unit_id=result["anchor_unit_id"],
            units=[SectionContentUnit.from_entity(unit) for unit in result["units"]],
        ),
    }

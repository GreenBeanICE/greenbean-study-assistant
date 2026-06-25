"""Provider 配置接口控制器（FastAPI APIRouter）。"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError

from app.api.dependencies import get_provider_service
from app.enums.purpose import Purpose
from app.schemas.provider_schema import (
    ProviderActivateResponse,
    ProviderConfigCreateRequest,
    ProviderConfigResponse,
    ProviderConfigUpdateRequest,
)
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["Providers"])


def _to_response(config) -> ProviderConfigResponse:
    return ProviderConfigResponse(
        id=config.id,
        name=config.name,
        api_mode=config.api_mode,
        api_host=config.api_host,
        api_path=config.api_path,
        model_id=config.model_id,
        display_name=config.display_name,
        context_window=config.context_window,
        max_output_tokens=config.max_output_tokens,
        purpose=config.purpose,
        embedding_dimension=config.embedding_dimension,
        is_active=config.is_active,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


def _to_activate_response(config) -> ProviderActivateResponse:
    return ProviderActivateResponse(
        id=config.id,
        name=config.name,
        display_name=config.display_name,
        model_id=config.model_id,
    )


@router.get("")
async def list_providers(
    purpose: Annotated[Purpose | None, Query()] = None,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    return {
        "code": 200,
        "data": [_to_response(c).model_dump(mode="json") for c in service.list_all(purpose)],
    }


@router.get("/active")
async def get_active_provider(
    purpose: Annotated[Purpose, Query()],
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    config = service.get_active(purpose)
    if config is None:
        raise HTTPException(status_code=404, detail="没有已激活的 provider")
    return {"code": 200, "data": _to_activate_response(config).model_dump(mode="json")}


@router.get("/{config_id}")
async def get_provider(
    config_id: str,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    config = service.get_by_id(config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="provider 不存在")
    return {"code": 200, "data": _to_response(config).model_dump(mode="json")}


@router.post("")
async def create_provider(
    request: ProviderConfigCreateRequest,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    try:
        config = service.create(request.model_dump())
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    return {"code": 200, "data": _to_response(config).model_dump(mode="json")}


@router.patch("/{config_id}")
async def update_provider(
    config_id: str,
    request: ProviderConfigUpdateRequest,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    try:
        config = service.update(config_id, request.model_dump(exclude_none=True))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    if config is None:
        raise HTTPException(status_code=404, detail="provider 不存在")
    return {"code": 200, "data": _to_response(config).model_dump(mode="json")}


@router.delete("/{config_id}")
async def delete_provider(
    config_id: str,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    return {"code": 200, "data": service.delete(config_id)}


@router.post("/{config_id}/activate")
async def activate_provider(
    config_id: str,
    service: Annotated[ProviderService, Depends(get_provider_service)] = None,
):
    config = service.activate(config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="provider 不存在")
    return {"code": 200, "data": _to_activate_response(config).model_dump(mode="json")}

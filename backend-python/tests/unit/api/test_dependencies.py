"""API 依赖注入测试。

验证未装配 session factory 时依赖函数显式抛 RuntimeError，
不静默降级为内存模式。
"""
import pytest

from app.api.dependencies import (
    get_document_query_service,
    get_ingest_service,
    set_session_factory,
)


@pytest.fixture(autouse=True)
def _reset_session_factory():
    yield
    set_session_factory(None)


@pytest.mark.unit
def test_get_ingest_service_raises_when_not_configured():
    set_session_factory(None)
    with pytest.raises(RuntimeError, match="Session factory is not configured"):
        get_ingest_service()


@pytest.mark.unit
def test_get_document_query_service_raises_when_not_configured():
    set_session_factory(None)
    with pytest.raises(RuntimeError, match="Session factory is not configured"):
        get_document_query_service()

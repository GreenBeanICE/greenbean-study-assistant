"""API 依赖注入集中装配。

提供 session factory、UOW factory、ingest service 和 query service，
避免 controller 内部分散 new 依赖。
"""
from app.services.document_ingest_service import DocumentIngestService
from app.services.document_query_service import DocumentQueryService

_session_factory = None


def set_session_factory(factory) -> None:
    """设置 app-level session factory，供 service 装配使用。"""
    global _session_factory
    _session_factory = factory


def _build_uow_factory():
    if _session_factory is None:
        raise RuntimeError(
            "Session factory is not configured. "
            "Call set_session_factory() at application startup."
        )
    from app.db.unit_of_work import SqlAlchemyUnitOfWork

    return lambda: SqlAlchemyUnitOfWork(_session_factory)


def get_ingest_service() -> DocumentIngestService:
    return DocumentIngestService(uow_factory=_build_uow_factory())


def get_document_query_service() -> DocumentQueryService:
    return DocumentQueryService(uow_factory=_build_uow_factory())

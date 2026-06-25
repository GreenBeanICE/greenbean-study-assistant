"""API 依赖注入集中装配。

提供 session factory、UOW factory、ingest service 和 query service，
避免 controller 内部分散 new 依赖。
"""
from app.config.settings import PROVIDER_CONFIGS_PATH
from app.repositories.provider_config_repository import ProviderConfigRepository
from app.services.chunk_service import ChunkService
from app.services.document_ingest_service import DocumentIngestService
from app.services.document_query_service import DocumentQueryService
from app.services.embedding_service import EmbeddingService
from app.services.provider_service import ProviderService
from app.services.section_service import SectionService

_session_factory = None
_provider_service: ProviderService | None = None


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
    return DocumentIngestService(
        uow_factory=_build_uow_factory(),
        chunk_service=get_chunk_service(),
        embedding_service=get_embedding_service(),
        section_service=get_section_service(),
    )


def get_document_query_service() -> DocumentQueryService:
    return DocumentQueryService(uow_factory=_build_uow_factory())


def get_chunk_service() -> ChunkService:
    return ChunkService(uow_factory=_build_uow_factory())


def get_section_service() -> SectionService:
    return SectionService(uow_factory=_build_uow_factory())


def get_provider_service() -> ProviderService:
    global _provider_service
    if _provider_service is None:
        _provider_service = ProviderService(
            ProviderConfigRepository(PROVIDER_CONFIGS_PATH)
        )
    return _provider_service


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService(uow_factory=_build_uow_factory())

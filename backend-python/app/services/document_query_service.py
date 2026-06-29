"""文档查询服务，负责文档列表和详情的只读查询。

通过 UOW session 创建 repository 进行查询，只读不写，不调用 commit。
"""
from app.entities import DocumentRecord, DocumentUnit


class DocumentQueryService:
    """文档只读查询服务。"""

    def __init__(self, uow_factory) -> None:
        self.uow_factory = uow_factory

    def list_by_workspace(self, workspace_id: str) -> list[DocumentRecord]:
        from app.repositories.document_repository import DocumentRepository

        with self.uow_factory() as uow:
            return DocumentRepository(uow.session).list_by_workspace(workspace_id)

    def get_document_detail(self, document_id: str) -> dict[str, DocumentRecord | list[DocumentUnit]] | None:
        from app.repositories.document_repository import DocumentRepository
        from app.repositories.document_unit_repository import DocumentUnitRepository

        with self.uow_factory() as uow:
            document = DocumentRepository(uow.session).get_by_id(document_id)
            if document is None:
                return None
            units = DocumentUnitRepository(uow.session).list_by_document(document_id)
            return {"document": document, "units": units}

    def delete_document(self, document_id: str) -> bool:
        from app.repositories.document_repository import DocumentRepository

        with self.uow_factory() as uow:
            deleted = DocumentRepository(uow.session).delete_by_id(document_id)
            uow.commit()
            return deleted

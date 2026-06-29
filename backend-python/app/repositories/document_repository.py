from sqlalchemy.orm import Session

from app.db.models import DocumentRecordModel
from app.entities import DocumentRecord
from app.repositories.sqlite_helpers import datetime_value, enum_value


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, document: DocumentRecord) -> DocumentRecord:
        model = self.session.get(DocumentRecordModel, document.id)
        if model is None:
            model = DocumentRecordModel(
                id=document.id,
                created_at=datetime_value(document.created_at),
            )
            self.session.add(model)
        model.workspace_id = document.workspace_id
        model.title = document.title
        model.original_filename = document.original_filename
        model.file_type = enum_value(document.file_type)
        model.file_path = document.file_path
        model.file_hash = document.file_hash
        model.status = enum_value(document.status)
        model.page_count = document.page_count
        model.updated_at = datetime_value(document.updated_at)
        return document

    def get_by_id(self, document_id: str) -> DocumentRecord | None:
        model = self.session.get(DocumentRecordModel, document_id)
        if model is None:
            return None
        return self._to_entity(model)

    def list_by_workspace(self, workspace_id: str) -> list[DocumentRecord]:
        models = (
            self.session.query(DocumentRecordModel)
            .filter(DocumentRecordModel.workspace_id == workspace_id)
            .order_by(DocumentRecordModel.created_at, DocumentRecordModel.id)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def delete_by_id(self, document_id: str) -> bool:
        from app.db.models import (
            AnalysisResultModel,
            ChunkModel,
            DocumentUnitModel,
            EmbeddingVectorModel,
            SectionModel,
            SectionUnitLinkModel,
        )

        model = self.session.get(DocumentRecordModel, document_id)
        if model is None:
            return False

        unit_ids = [
            row.id
            for row in self.session.query(DocumentUnitModel.id)
            .filter(DocumentUnitModel.document_id == document_id)
            .all()
        ]
        section_ids = [
            row.id
            for row in self.session.query(SectionModel.id)
            .filter(SectionModel.document_id == document_id)
            .all()
        ]

        if unit_ids:
            chunk_ids = [
                row.id
                for row in self.session.query(ChunkModel.id)
                .filter(ChunkModel.document_unit_id.in_(unit_ids))
                .all()
            ]
            if chunk_ids:
                self.session.query(EmbeddingVectorModel).filter(
                    EmbeddingVectorModel.chunk_id.in_(chunk_ids)
                ).delete(synchronize_session=False)
            self.session.query(ChunkModel).filter(
                ChunkModel.document_unit_id.in_(unit_ids)
            ).delete(synchronize_session=False)

        if section_ids:
            self.session.query(SectionUnitLinkModel).filter(
                SectionUnitLinkModel.section_id.in_(section_ids)
            ).delete(synchronize_session=False)
        self.session.query(SectionModel).filter(
            SectionModel.document_id == document_id
        ).delete(synchronize_session=False)
        self.session.query(AnalysisResultModel).filter(
            AnalysisResultModel.document_id == document_id
        ).delete(synchronize_session=False)
        self.session.query(DocumentUnitModel).filter(
            DocumentUnitModel.document_id == document_id
        ).delete(synchronize_session=False)

        self.session.delete(model)
        return True

    def _to_entity(self, model: DocumentRecordModel) -> DocumentRecord:
        return DocumentRecord(
            id=model.id,
            workspace_id=model.workspace_id,
            title=model.title,
            original_filename=model.original_filename,
            file_type=model.file_type,
            file_path=model.file_path,
            file_hash=model.file_hash,
            status=model.status,
            page_count=model.page_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

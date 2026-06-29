from sqlalchemy.orm import Session

from app.db.models import SectionModel
from app.entities import Section
from app.repositories.sqlite_helpers import datetime_value, json_object, json_value


class SectionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, section: Section) -> Section:
        model = self.session.get(SectionModel, section.id)
        if model is None:
            model = SectionModel(
                id=section.id,
                created_at=datetime_value(section.created_at),
            )
            self.session.add(model)
        model.document_id = section.document_id
        model.parent_section_id = section.parent_section_id
        model.title = section.title
        model.level = section.level
        model.order_index = section.order_index
        model.start_page = section.start_page
        model.end_page = section.end_page
        model.summary = section.summary
        model.metadata_json = json_value(section.metadata_json)
        model.parser_name = section.parser_name
        model.parser_version = section.parser_version
        model.external_id = section.external_id
        return section

    def get_by_id(self, section_id: str) -> Section | None:
        model = self.session.get(SectionModel, section_id)
        if model is None:
            return None
        return self._to_entity(model)

    def list_by_document(self, document_id: str) -> list[Section]:
        models = (
            self.session.query(SectionModel)
            .filter(SectionModel.document_id == document_id)
            .order_by(SectionModel.order_index, SectionModel.id)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def delete_by_document(self, document_id: str) -> None:
        (
            self.session.query(SectionModel)
            .filter(SectionModel.document_id == document_id)
            .delete(synchronize_session=False)
        )

    def _to_entity(self, model: SectionModel) -> Section:
        return Section(
            id=model.id,
            document_id=model.document_id,
            parent_section_id=model.parent_section_id,
            title=model.title,
            level=model.level,
            order_index=model.order_index,
            start_page=model.start_page,
            end_page=model.end_page,
            summary=model.summary,
            metadata_json=json_object(model.metadata_json),
            parser_name=model.parser_name,
            parser_version=model.parser_version,
            external_id=model.external_id,
            created_at=model.created_at,
        )

from sqlalchemy.orm import Session

from app.db.models import SectionUnitLinkModel
from app.entities import SectionUnitLink


class SectionUnitLinkRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, link: SectionUnitLink) -> SectionUnitLink:
        model = self.session.get(SectionUnitLinkModel, link.id)
        if model is None:
            model = SectionUnitLinkModel(id=link.id)
            self.session.add(model)
        model.section_id = link.section_id
        model.document_unit_id = link.document_unit_id
        model.order_index = link.order_index
        return link

    def list_by_section(self, section_id: str) -> list[SectionUnitLink]:
        models = (
            self.session.query(SectionUnitLinkModel)
            .filter(SectionUnitLinkModel.section_id == section_id)
            .order_by(SectionUnitLinkModel.order_index)
            .all()
        )
        return [
            SectionUnitLink(
                id=model.id,
                section_id=model.section_id,
                document_unit_id=model.document_unit_id,
                order_index=model.order_index,
            )
            for model in models
        ]

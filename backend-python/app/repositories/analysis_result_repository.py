from sqlalchemy.orm import Session

from app.db.models import AnalysisResultModel
from app.entities import AnalysisResult
from app.repositories.sqlite_helpers import datetime_value, enum_value, json_object, json_value


class AnalysisResultRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, result: AnalysisResult) -> AnalysisResult:
        model = self.session.get(AnalysisResultModel, result.id)
        if model is None:
            model = AnalysisResultModel(
                id=result.id,
                created_at=datetime_value(result.created_at),
            )
            self.session.add(model)
        model.document_id = result.document_id
        model.section_id = result.section_id
        model.analysis_type = enum_value(result.analysis_type)
        model.language = result.language
        model.content_markdown = result.content_markdown
        model.content_json = json_value(result.content_json)
        model.model_name = result.model_name
        model.prompt_version = result.prompt_version
        model.updated_at = datetime_value(result.updated_at)
        return result

    def get_by_id(self, result_id: str) -> AnalysisResult | None:
        model = self.session.get(AnalysisResultModel, result_id)
        if model is None:
            return None
        return self._to_entity(model)

    def get_by_section_id(self, section_id: str) -> AnalysisResult | None:
        model = (
            self.session.query(AnalysisResultModel)
            .filter(AnalysisResultModel.section_id == section_id)
            .one_or_none()
        )
        if model is None:
            return None
        return self._to_entity(model)

    def _to_entity(self, model: AnalysisResultModel) -> AnalysisResult:
        return AnalysisResult(
            id=model.id,
            document_id=model.document_id,
            section_id=model.section_id,
            analysis_type=model.analysis_type,
            language=model.language,
            content_markdown=model.content_markdown,
            content_json=json_object(model.content_json),
            model_name=model.model_name,
            prompt_version=model.prompt_version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

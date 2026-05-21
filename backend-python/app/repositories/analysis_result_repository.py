import sqlite3

from app.entities import AnalysisResult
from app.repositories.sqlite_helpers import datetime_value, enum_value, json_object, json_value


class AnalysisResultRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, result: AnalysisResult) -> AnalysisResult:
        self.connection.execute(
            """
            INSERT INTO analysis_results (
                id, document_id, section_id, analysis_type, language,
                content_markdown, content_json, model_name, prompt_version,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                document_id = excluded.document_id,
                section_id = excluded.section_id,
                analysis_type = excluded.analysis_type,
                language = excluded.language,
                content_markdown = excluded.content_markdown,
                content_json = excluded.content_json,
                model_name = excluded.model_name,
                prompt_version = excluded.prompt_version,
                updated_at = excluded.updated_at
            """,
            (
                result.id,
                result.document_id,
                result.section_id,
                enum_value(result.analysis_type),
                result.language,
                result.content_markdown,
                json_value(result.content_json),
                result.model_name,
                result.prompt_version,
                datetime_value(result.created_at),
                datetime_value(result.updated_at),
            ),
        )
        self.connection.commit()
        return result

    def get_by_id(self, result_id: str) -> AnalysisResult | None:
        row = self.connection.execute(
            """
            SELECT id, document_id, section_id, analysis_type, language,
                   content_markdown, content_json, model_name, prompt_version,
                   created_at, updated_at
            FROM analysis_results
            WHERE id = ?
            """,
            (result_id,),
        ).fetchone()
        if row is None:
            return None
        return AnalysisResult(
            id=row[0],
            document_id=row[1],
            section_id=row[2],
            analysis_type=row[3],
            language=row[4],
            content_markdown=row[5],
            content_json=json_object(row[6]),
            model_name=row[7],
            prompt_version=row[8],
            created_at=row[9],
            updated_at=row[10],
        )

import sqlite3

from app.entities import DocumentUnit
from app.repositories.sqlite_helpers import datetime_value, json_object, json_value


class DocumentUnitRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, unit: DocumentUnit) -> DocumentUnit:
        self.connection.execute(
            """
            INSERT INTO document_units (
                id, document_id, sequence_index, text_content, page_number,
                start_char, end_char, token_count, metadata_json, raw_content_json,
                parser_name, parser_version, external_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                document_id = excluded.document_id,
                sequence_index = excluded.sequence_index,
                text_content = excluded.text_content,
                page_number = excluded.page_number,
                start_char = excluded.start_char,
                end_char = excluded.end_char,
                token_count = excluded.token_count,
                metadata_json = excluded.metadata_json,
                raw_content_json = excluded.raw_content_json,
                parser_name = excluded.parser_name,
                parser_version = excluded.parser_version,
                external_id = excluded.external_id
            """,
            (
                unit.id,
                unit.document_id,
                unit.sequence_index,
                unit.text_content,
                unit.page_number,
                unit.start_char,
                unit.end_char,
                unit.token_count,
                json_value(unit.metadata_json),
                json_value(unit.raw_content_json),
                unit.parser_name,
                unit.parser_version,
                unit.external_id,
                datetime_value(unit.created_at),
            ),
        )
        self.connection.commit()
        return unit

    def get_by_id(self, unit_id: str) -> DocumentUnit | None:
        row = self.connection.execute(
            """
            SELECT id, document_id, sequence_index, text_content, page_number,
                   start_char, end_char, token_count, metadata_json, raw_content_json,
                   parser_name, parser_version, external_id, created_at
            FROM document_units
            WHERE id = ?
            """,
            (unit_id,),
        ).fetchone()
        if row is None:
            return None
        return DocumentUnit(
            id=row[0],
            document_id=row[1],
            sequence_index=row[2],
            text_content=row[3],
            page_number=row[4],
            start_char=row[5],
            end_char=row[6],
            token_count=row[7],
            metadata_json=json_object(row[8]),
            raw_content_json=json_object(row[9]),
            parser_name=row[10],
            parser_version=row[11],
            external_id=row[12],
            created_at=row[13],
        )

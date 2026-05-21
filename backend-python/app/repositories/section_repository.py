import sqlite3

from app.entities import Section
from app.repositories.sqlite_helpers import datetime_value, json_object, json_value


class SectionRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, section: Section) -> Section:
        self.connection.execute(
            """
            INSERT INTO sections (
                id, document_id, parent_section_id, title, level, order_index,
                start_page, end_page, summary, metadata_json, parser_name,
                parser_version, external_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                document_id = excluded.document_id,
                parent_section_id = excluded.parent_section_id,
                title = excluded.title,
                level = excluded.level,
                order_index = excluded.order_index,
                start_page = excluded.start_page,
                end_page = excluded.end_page,
                summary = excluded.summary,
                metadata_json = excluded.metadata_json,
                parser_name = excluded.parser_name,
                parser_version = excluded.parser_version,
                external_id = excluded.external_id
            """,
            (
                section.id,
                section.document_id,
                section.parent_section_id,
                section.title,
                section.level,
                section.order_index,
                section.start_page,
                section.end_page,
                section.summary,
                json_value(section.metadata_json),
                section.parser_name,
                section.parser_version,
                section.external_id,
                datetime_value(section.created_at),
            ),
        )
        self.connection.commit()
        return section

    def get_by_id(self, section_id: str) -> Section | None:
        row = self.connection.execute(
            """
            SELECT id, document_id, parent_section_id, title, level, order_index,
                   start_page, end_page, summary, metadata_json, parser_name,
                   parser_version, external_id, created_at
            FROM sections
            WHERE id = ?
            """,
            (section_id,),
        ).fetchone()
        if row is None:
            return None
        return Section(
            id=row[0],
            document_id=row[1],
            parent_section_id=row[2],
            title=row[3],
            level=row[4],
            order_index=row[5],
            start_page=row[6],
            end_page=row[7],
            summary=row[8],
            metadata_json=json_object(row[9]),
            parser_name=row[10],
            parser_version=row[11],
            external_id=row[12],
            created_at=row[13],
        )

import sqlite3

from app.entities import DocumentRecord
from app.repositories.sqlite_helpers import datetime_value, enum_value


class DocumentRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, document: DocumentRecord) -> DocumentRecord:
        self.connection.execute(
            """
            INSERT INTO document_records (
                id, workspace_id, title, original_filename, file_type, file_path,
                file_hash, status, page_count, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                workspace_id = excluded.workspace_id,
                title = excluded.title,
                original_filename = excluded.original_filename,
                file_type = excluded.file_type,
                file_path = excluded.file_path,
                file_hash = excluded.file_hash,
                status = excluded.status,
                page_count = excluded.page_count,
                updated_at = excluded.updated_at
            """,
            (
                document.id,
                document.workspace_id,
                document.title,
                document.original_filename,
                enum_value(document.file_type),
                document.file_path,
                document.file_hash,
                enum_value(document.status),
                document.page_count,
                datetime_value(document.created_at),
                datetime_value(document.updated_at),
            ),
        )
        self.connection.commit()
        return document

    def get_by_id(self, document_id: str) -> DocumentRecord | None:
        row = self.connection.execute(
            """
            SELECT id, workspace_id, title, original_filename, file_type, file_path,
                   file_hash, status, page_count, created_at, updated_at
            FROM document_records
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()
        if row is None:
            return None
        return DocumentRecord(
            id=row[0],
            workspace_id=row[1],
            title=row[2],
            original_filename=row[3],
            file_type=row[4],
            file_path=row[5],
            file_hash=row[6],
            status=row[7],
            page_count=row[8],
            created_at=row[9],
            updated_at=row[10],
        )

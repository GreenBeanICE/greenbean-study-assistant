import sqlite3

from app.entities import ChatSession
from app.repositories.sqlite_helpers import datetime_value


class ChatSessionRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, session: ChatSession) -> ChatSession:
        self.connection.execute(
            """
            INSERT INTO chat_sessions (
                id, workspace_id, document_id, title, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                workspace_id = excluded.workspace_id,
                document_id = excluded.document_id,
                title = excluded.title,
                updated_at = excluded.updated_at
            """,
            (
                session.id,
                session.workspace_id,
                session.document_id,
                session.title,
                datetime_value(session.created_at),
                datetime_value(session.updated_at),
            ),
        )
        self.connection.commit()
        return session

    def get_by_id(self, session_id: str) -> ChatSession | None:
        row = self.connection.execute(
            """
            SELECT id, workspace_id, document_id, title, created_at, updated_at
            FROM chat_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return ChatSession(
            id=row[0],
            workspace_id=row[1],
            document_id=row[2],
            title=row[3],
            created_at=row[4],
            updated_at=row[5],
        )

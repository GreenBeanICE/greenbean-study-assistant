import sqlite3

from app.entities import ChatMessage
from app.repositories.sqlite_helpers import datetime_value, enum_value, json_object, json_value


class ChatMessageRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, message: ChatMessage) -> ChatMessage:
        self.connection.execute(
            """
            INSERT INTO chat_messages (
                id, session_id, role, content, source_context_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                session_id = excluded.session_id,
                role = excluded.role,
                content = excluded.content,
                source_context_json = excluded.source_context_json
            """,
            (
                message.id,
                message.session_id,
                enum_value(message.role),
                message.content,
                json_value(message.source_context_json),
                datetime_value(message.created_at),
            ),
        )
        self.connection.commit()
        return message

    def get_by_id(self, message_id: str) -> ChatMessage | None:
        row = self.connection.execute(
            """
            SELECT id, session_id, role, content, source_context_json, created_at
            FROM chat_messages
            WHERE id = ?
            """,
            (message_id,),
        ).fetchone()
        if row is None:
            return None
        return ChatMessage(
            id=row[0],
            session_id=row[1],
            role=row[2],
            content=row[3],
            source_context_json=json_object(row[4]),
            created_at=row[5],
        )

from sqlalchemy.orm import Session

from app.db.models import ChatMessageModel
from app.entities import ChatMessage
from app.repositories.sqlite_helpers import datetime_value, enum_value, json_object, json_value


class ChatMessageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, message: ChatMessage) -> ChatMessage:
        model = self.session.get(ChatMessageModel, message.id)
        if model is None:
            model = ChatMessageModel(
                id=message.id,
                created_at=datetime_value(message.created_at),
            )
            self.session.add(model)
        model.session_id = message.session_id
        model.role = enum_value(message.role)
        model.content = message.content
        model.source_context_json = json_value(message.source_context_json)
        return message

    def get_by_id(self, message_id: str) -> ChatMessage | None:
        model = self.session.get(ChatMessageModel, message_id)
        if model is None:
            return None
        return ChatMessage(
            id=model.id,
            session_id=model.session_id,
            role=model.role,
            content=model.content,
            source_context_json=json_object(model.source_context_json),
            created_at=model.created_at,
        )

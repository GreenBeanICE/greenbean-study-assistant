from sqlalchemy.orm import Session

from app.db.models import ChatSessionModel
from app.entities import ChatSession
from app.repositories.sqlite_helpers import datetime_value


class ChatSessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, session: ChatSession) -> ChatSession:
        model = self.session.get(ChatSessionModel, session.id)
        if model is None:
            model = ChatSessionModel(
                id=session.id,
                created_at=datetime_value(session.created_at),
            )
            self.session.add(model)
        model.workspace_id = session.workspace_id
        model.document_id = session.document_id
        model.title = session.title
        model.updated_at = datetime_value(session.updated_at)
        return session

    def get_by_id(self, session_id: str) -> ChatSession | None:
        model = self.session.get(ChatSessionModel, session_id)
        if model is None:
            return None
        return ChatSession(
            id=model.id,
            workspace_id=model.workspace_id,
            document_id=model.document_id,
            title=model.title,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

from types import TracebackType

from sqlalchemy.orm import Session

from app.db.orm import SessionFactory


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: SessionFactory) -> None:
        self.session_factory = session_factory
        self.session: Session

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self.session_factory()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if self.session.in_transaction():
                self.session.rollback()
        finally:
            self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

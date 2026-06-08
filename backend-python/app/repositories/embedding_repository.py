from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.db.models import ChunkModel, EmbeddingVectorModel
from app.repositories.sqlite_helpers import datetime_value, json_array, json_value


class EmbeddingDimensionError(ValueError):
    pass


class MissingChunkError(ValueError):
    pass


@dataclass(frozen=True)
class ChunkEmbedding:
    id: str
    chunk_id: str
    embedding_model: str
    vector_dimension: int
    vector: list[float]
    created_at: datetime


class EmbeddingRepository:
    def __init__(self, session: Session, *, embedding_dimension: int) -> None:
        self.session = session
        self.embedding_dimension = embedding_dimension

    def save_for_chunk(
        self,
        *,
        chunk_id: str,
        embedding_model: str,
        vector: list[float],
    ) -> ChunkEmbedding:
        if len(vector) != self.embedding_dimension:
            raise EmbeddingDimensionError(
                f"embedding vector dimension must be {self.embedding_dimension}, got {len(vector)}"
            )
        self.session.flush()
        if not self._chunk_exists(chunk_id):
            raise MissingChunkError(f"Chunk does not exist: {chunk_id}")

        embedding = ChunkEmbedding(
            id=str(uuid4()),
            chunk_id=chunk_id,
            embedding_model=embedding_model,
            vector_dimension=self.embedding_dimension,
            vector=vector,
            created_at=datetime.now(timezone.utc),
        )
        embedding_table = EmbeddingVectorModel.__table__
        statement = insert(embedding_table).values(
            id=embedding.id,
            chunk_id=embedding.chunk_id,
            embedding_model=embedding.embedding_model,
            vector_dimension=embedding.vector_dimension,
            vector_json=json_value(embedding.vector),
            created_at=datetime_value(embedding.created_at),
        )
        statement = statement.on_conflict_do_update(
            index_elements=[embedding_table.c.chunk_id],
            set_={
                "embedding_model": statement.excluded.embedding_model,
                "vector_dimension": statement.excluded.vector_dimension,
                "vector_json": statement.excluded.vector_json,
                "created_at": statement.excluded.created_at,
            },
        )
        self.session.execute(statement)
        self.session.execute(
            update(ChunkModel.__table__)
            .where(ChunkModel.__table__.c.id == embedding.chunk_id)
            .values(
                embedding_model=embedding.embedding_model,
                embedding_dimension=embedding.vector_dimension,
                embedding_created_at=datetime_value(embedding.created_at),
            )
        )
        return embedding

    def get_by_chunk_id(self, chunk_id: str) -> ChunkEmbedding | None:
        table = EmbeddingVectorModel.__table__
        row = self.session.execute(
            select(
                table.c.id,
                table.c.chunk_id,
                table.c.embedding_model,
                table.c.vector_dimension,
                table.c.vector_json,
                table.c.created_at,
            ).where(table.c.chunk_id == chunk_id)
        ).one_or_none()
        if row is None:
            return None
        return ChunkEmbedding(
            id=row[0],
            chunk_id=row[1],
            embedding_model=row[2],
            vector_dimension=row[3],
            vector=json_array(row[4]),
            created_at=datetime.fromisoformat(row[5]),
        )

    def _chunk_exists(self, chunk_id: str) -> bool:
        table = ChunkModel.__table__
        return (
            self.session.execute(
                select(table.c.id).where(table.c.id == chunk_id)
            ).scalar_one_or_none()
            is not None
        )

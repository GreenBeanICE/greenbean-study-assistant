from dataclasses import dataclass
from datetime import datetime, timezone
import sqlite3
from uuid import uuid4

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
    def __init__(self, connection: sqlite3.Connection, *, embedding_dimension: int) -> None:
        self.connection = connection
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
        self.connection.execute(
            """
            INSERT INTO embedding_vectors (
                id, chunk_id, embedding_model, vector_dimension, vector_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chunk_id) DO UPDATE SET
                embedding_model = excluded.embedding_model,
                vector_dimension = excluded.vector_dimension,
                vector_json = excluded.vector_json,
                created_at = excluded.created_at
            """,
            (
                embedding.id,
                embedding.chunk_id,
                embedding.embedding_model,
                embedding.vector_dimension,
                json_value(embedding.vector),
                datetime_value(embedding.created_at),
            ),
        )
        self.connection.execute(
            """
            UPDATE chunks
            SET embedding_model = ?, embedding_dimension = ?, embedding_created_at = ?
            WHERE id = ?
            """,
            (
                embedding.embedding_model,
                embedding.vector_dimension,
                datetime_value(embedding.created_at),
                embedding.chunk_id,
            ),
        )
        self.connection.commit()
        return embedding

    def get_by_chunk_id(self, chunk_id: str) -> ChunkEmbedding | None:
        row = self.connection.execute(
            """
            SELECT id, chunk_id, embedding_model, vector_dimension, vector_json, created_at
            FROM embedding_vectors
            WHERE chunk_id = ?
            """,
            (chunk_id,),
        ).fetchone()
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
        row = self.connection.execute("SELECT 1 FROM chunks WHERE id = ?", (chunk_id,)).fetchone()
        return row is not None

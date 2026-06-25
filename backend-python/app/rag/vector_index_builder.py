from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ChunkModel
from app.repositories.embedding_repository import EmbeddingRepository


class MissingIndexedChunkError(ValueError):
    pass


class SQLiteVecIndexBuilder:
    def __init__(self, *, session: Session, embedding_dimension: int) -> None:
        if embedding_dimension <= 0:
            raise ValueError("embedding_dimension must be greater than 0")
        self.session = session
        self.embedding_dimension = embedding_dimension

    def upsert_chunk_embedding(
        self,
        *,
        chunk_id: str,
        vector: list[float],
        embedding_model: str,
    ) -> None:
        if len(vector) != self.embedding_dimension:
            raise ValueError(
                f"embedding vector dimension must be {self.embedding_dimension}, got {len(vector)}"
            )
        self.session.flush()
        if not self._chunk_exists(chunk_id):
            raise MissingIndexedChunkError(f"Chunk does not exist: {chunk_id}")

        EmbeddingRepository(
            self.session,
            embedding_dimension=self.embedding_dimension,
        ).save_for_chunk(
            chunk_id=chunk_id,
            embedding_model=embedding_model,
            vector=vector,
        )

        rowid = self._upsert_index_entry(
            chunk_id=chunk_id,
            embedding_model=embedding_model,
        )
        connection = self.session.connection()
        connection.exec_driver_sql(
            "DELETE FROM chunk_embedding_vec WHERE rowid = ?",
            (rowid,),
        )
        connection.exec_driver_sql(
            "INSERT INTO chunk_embedding_vec(rowid, embedding) VALUES (?, ?)",
            (rowid, _serialize_float32(vector)),
        )

    def _chunk_exists(self, chunk_id: str) -> bool:
        return (
            self.session.execute(
                select(ChunkModel.id).where(ChunkModel.id == chunk_id)
            ).scalar_one_or_none()
            is not None
        )

    def _upsert_index_entry(self, *, chunk_id: str, embedding_model: str) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        connection = self.session.connection()
        connection.exec_driver_sql(
            """
            INSERT INTO chunk_embedding_index_entries(
                chunk_id,
                embedding_model,
                vector_dimension,
                created_at
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chunk_id) DO UPDATE SET
                embedding_model = excluded.embedding_model,
                vector_dimension = excluded.vector_dimension,
                created_at = excluded.created_at
            """,
            (chunk_id, embedding_model, self.embedding_dimension, created_at),
        )
        row = connection.exec_driver_sql(
            "SELECT rowid FROM chunk_embedding_index_entries WHERE chunk_id = ?",
            (chunk_id,),
        ).one()
        return int(row[0])


def _serialize_float32(vector: list[float]) -> bytes:
    try:
        import sqlite_vec

        return sqlite_vec.serialize_float32(vector)
    except ModuleNotFoundError:
        import struct

        return struct.pack(f"{len(vector)}f", *vector)

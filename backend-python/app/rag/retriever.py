from dataclasses import dataclass
import json
from typing import Any, Protocol

from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ChunkSearchResult:
    chunk_id: str
    document_unit_id: str
    text_content: str
    page_number: int | None
    distance: float
    metadata_json: dict[str, Any] | None


class VectorIndex(Protocol):
    def search(self, *, query_vector: list[float], top_k: int) -> list[ChunkSearchResult]:
        pass


class Retriever:
    def __init__(self, *, vector_index: VectorIndex) -> None:
        self.vector_index = vector_index

    def retrieve(self, *, query_vector: list[float], top_k: int) -> list[ChunkSearchResult]:
        return self.vector_index.search(query_vector=query_vector, top_k=top_k)


class SQLiteVecRetriever:
    def __init__(self, *, session: Session, embedding_dimension: int) -> None:
        if embedding_dimension <= 0:
            raise ValueError("embedding_dimension must be greater than 0")
        self.session = session
        self.embedding_dimension = embedding_dimension

    def search(self, *, query_vector: list[float], top_k: int) -> list[ChunkSearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")
        if len(query_vector) != self.embedding_dimension:
            raise ValueError(
                f"query vector dimension must be {self.embedding_dimension}, got {len(query_vector)}"
            )

        rows = self.session.connection().exec_driver_sql(
            """
            SELECT
                entry.chunk_id,
                chunk.document_unit_id,
                chunk.text_content,
                document_unit.page_number,
                vec.distance,
                chunk.metadata_json
            FROM chunk_embedding_vec AS vec
            JOIN chunk_embedding_index_entries AS entry ON entry.rowid = vec.rowid
            JOIN chunks AS chunk ON chunk.id = entry.chunk_id
            JOIN document_units AS document_unit ON document_unit.id = chunk.document_unit_id
            WHERE vec.embedding MATCH ? AND k = ?
            ORDER BY vec.distance
            """,
            (_serialize_float32(query_vector), top_k),
        )
        return [
            ChunkSearchResult(
                chunk_id=row[0],
                document_unit_id=row[1],
                text_content=row[2],
                page_number=row[3],
                distance=float(row[4]),
                metadata_json=json.loads(row[5]) if row[5] else None,
            )
            for row in rows
        ]


def _serialize_float32(vector: list[float]) -> bytes:
    try:
        import sqlite_vec

        return sqlite_vec.serialize_float32(vector)
    except ModuleNotFoundError:
        import struct

        return struct.pack(f"{len(vector)}f", *vector)

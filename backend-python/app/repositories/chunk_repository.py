import sqlite3

from app.entities import Chunk
from app.repositories.sqlite_helpers import datetime_value, json_object, json_value


class ChunkRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, chunk: Chunk) -> Chunk:
        self.connection.execute(
            """
            INSERT INTO chunks (
                id, document_unit_id, sequence_index, text_content, start_char,
                end_char, token_count, metadata_json, chunker_name, chunker_version,
                embedding_model, embedding_dimension, embedding_created_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                document_unit_id = excluded.document_unit_id,
                sequence_index = excluded.sequence_index,
                text_content = excluded.text_content,
                start_char = excluded.start_char,
                end_char = excluded.end_char,
                token_count = excluded.token_count,
                metadata_json = excluded.metadata_json,
                chunker_name = excluded.chunker_name,
                chunker_version = excluded.chunker_version,
                embedding_model = excluded.embedding_model,
                embedding_dimension = excluded.embedding_dimension,
                embedding_created_at = excluded.embedding_created_at
            """,
            (
                chunk.id,
                chunk.document_unit_id,
                chunk.sequence_index,
                chunk.text_content,
                chunk.start_char,
                chunk.end_char,
                chunk.token_count,
                json_value(chunk.metadata_json),
                chunk.chunker_name,
                chunk.chunker_version,
                chunk.embedding_model,
                chunk.embedding_dimension,
                datetime_value(chunk.embedding_created_at) if chunk.embedding_created_at else None,
                datetime_value(chunk.created_at),
            ),
        )
        self.connection.commit()
        return chunk

    def get_by_id(self, chunk_id: str) -> Chunk | None:
        row = self.connection.execute(
            """
            SELECT id, document_unit_id, sequence_index, text_content, start_char,
                   end_char, token_count, metadata_json, chunker_name, chunker_version,
                   embedding_model, embedding_dimension, embedding_created_at, created_at
            FROM chunks
            WHERE id = ?
            """,
            (chunk_id,),
        ).fetchone()
        if row is None:
            return None
        return Chunk(
            id=row[0],
            document_unit_id=row[1],
            sequence_index=row[2],
            text_content=row[3],
            start_char=row[4],
            end_char=row[5],
            token_count=row[6],
            metadata_json=json_object(row[7]),
            chunker_name=row[8],
            chunker_version=row[9],
            embedding_model=row[10],
            embedding_dimension=row[11],
            embedding_created_at=row[12],
            created_at=row[13],
        )

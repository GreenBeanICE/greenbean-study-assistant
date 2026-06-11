from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="Chunk unique ID.")
    document_unit_id: str = Field(..., description="Source DocumentUnit ID.")
    sequence_index: int = Field(
        ...,
        ge=0,
        description="Stable order of the chunk within its source DocumentUnit.",
    )
    text_content: str = Field(..., description="Text content used for RAG retrieval.")
    start_char: int | None = Field(default=None, ge=0, description="Start character offset in the source unit.")
    end_char: int | None = Field(default=None, ge=0, description="End character offset in the source unit.")
    token_count: int | None = Field(default=None, ge=0, description="Estimated token count for this chunk.")
    metadata_json: dict[str, Any] | None = Field(default=None, description="Chunk metadata for filtering or tracing.")
    chunker_name: str | None = Field(default=None, description="Name of the chunking component.")
    chunker_version: str | None = Field(default=None, description="Version of the chunking component.")
    embedding_model: str | None = Field(default=None, description="Embedding model used for this chunk.")
    embedding_dimension: int | None = Field(default=None, gt=0, description="Embedding vector dimension.")
    embedding_created_at: datetime | None = Field(default=None, description="Embedding creation time.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation time.")

    @field_validator("text_content")
    @classmethod
    def validate_text_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text_content must not be empty")
        return value

    @model_validator(mode="after")
    def validate_char_range(self) -> "Chunk":
        if self.start_char is not None and self.end_char is not None and self.end_char < self.start_char:
            raise ValueError("end_char must be greater than or equal to start_char")
        return self

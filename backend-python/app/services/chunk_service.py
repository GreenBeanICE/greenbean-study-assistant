from app.entities import Chunk, DocumentUnit


class FixedLengthChunker:
    name = "fixed-length"
    version = "0.1"

    def __init__(self, *, chunk_size: int) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        self.chunk_size = chunk_size

    def split_document_units(self, document_units: list[DocumentUnit]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for unit in sorted(document_units, key=lambda item: item.sequence_index):
            unit_sequence_index = 0
            for start_char in range(0, len(unit.text_content), self.chunk_size):
                end_char = min(start_char + self.chunk_size, len(unit.text_content))
                text_content = unit.text_content[start_char:end_char]
                if not text_content.strip():
                    continue
                chunks.append(
                    Chunk(
                        document_unit_id=unit.id,
                        sequence_index=unit_sequence_index,
                        text_content=text_content.strip(),
                        start_char=start_char,
                        end_char=end_char,
                        token_count=len(text_content.strip()),
                        metadata_json={
                            "document_id": unit.document_id,
                            "document_unit_sequence_index": unit.sequence_index,
                            "page_number": unit.page_number,
                            "source_metadata": unit.metadata_json,
                        },
                        chunker_name=self.name,
                        chunker_version=self.version,
                    )
                )
                unit_sequence_index += 1
        return chunks

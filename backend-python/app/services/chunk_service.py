from app.entities import Chunk


class ChunkService:
    def __init__(self, uow_factory, *, max_chunk_size: int = 800, overlap_chars: int = 100) -> None:
        if overlap_chars >= max_chunk_size:
            raise ValueError("overlap_chars must be smaller than max_chunk_size")
        self.uow_factory = uow_factory
        self.max_chunk_size = max_chunk_size
        self.overlap_chars = overlap_chars

    def split_units_into_chunks(self, units) -> list[Chunk]:
        chunks: list[Chunk] = []
        step = self.max_chunk_size - self.overlap_chars
        for unit in units:
            text = unit.text_content
            if not text.strip():
                continue

            sequence_index = 0
            for start in range(0, len(text), step):
                end = min(start + self.max_chunk_size, len(text))
                piece = text[start:end]
                if not piece.strip():
                    continue
                chunks.append(
                    Chunk(
                        document_unit_id=unit.id,
                        sequence_index=sequence_index,
                        text_content=piece,
                        start_char=start,
                        end_char=end,
                    )
                )
                sequence_index += 1
                if end == len(text):
                    break
        return chunks

    def build_chunks_for_document(self, document_id: str) -> list[Chunk]:
        from app.repositories.chunk_repository import ChunkRepository
        from app.repositories.document_unit_repository import DocumentUnitRepository

        with self.uow_factory() as uow:
            units = DocumentUnitRepository(uow.session).list_by_document(document_id)
            chunks = self.split_units_into_chunks(units)
            repo = ChunkRepository(uow.session)
            for chunk in chunks:
                repo.save(chunk)
            uow.commit()
            return chunks

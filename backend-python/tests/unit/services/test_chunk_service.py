"""固定长度 Chunk 切分测试。"""

import pytest

from app.entities import DocumentUnit
from app.services.chunk_service import FixedLengthChunker


def _unit(text_content: str) -> DocumentUnit:
    return DocumentUnit(
        id="unit-1",
        document_id="document-1",
        sequence_index=3,
        page_number=7,
        text_content=text_content,
        metadata_json={"language": "en"},
    )


def test_fixed_length_chunker_splits_text_with_offsets_and_page_trace():
    chunker = FixedLengthChunker(chunk_size=5)

    chunks = chunker.split_document_units([_unit("ABCDEFGHIJKL")])

    assert [chunk.text_content for chunk in chunks] == ["ABCDE", "FGHIJ", "KL"]
    assert [chunk.sequence_index for chunk in chunks] == [0, 1, 2]
    assert [(chunk.start_char, chunk.end_char) for chunk in chunks] == [
        (0, 5),
        (5, 10),
        (10, 12),
    ]
    assert all(chunk.document_unit_id == "unit-1" for chunk in chunks)
    assert all(chunk.chunker_name == "fixed-length" for chunk in chunks)
    assert chunks[0].metadata_json == {
        "document_id": "document-1",
        "document_unit_sequence_index": 3,
        "page_number": 7,
        "source_metadata": {"language": "en"},
    }


def test_fixed_length_chunker_skips_whitespace_only_slices():
    chunker = FixedLengthChunker(chunk_size=3)

    chunks = chunker.split_document_units([_unit("ABC   DEF")])

    assert [chunk.text_content for chunk in chunks] == ["ABC", "DEF"]
    assert [(chunk.start_char, chunk.end_char) for chunk in chunks] == [(0, 3), (6, 9)]


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_fixed_length_chunker_rejects_invalid_chunk_size(chunk_size):
    with pytest.raises(ValueError, match="chunk_size"):
        FixedLengthChunker(chunk_size=chunk_size)

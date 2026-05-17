from enum import Enum


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    INDEXED = "indexed"
    FAILED = "failed"

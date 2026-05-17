from enum import Enum


class DocumentFileType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    DOCX = "docx"
    PPTX = "pptx"
    OTHER = "other"

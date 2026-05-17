from enum import Enum


class AnalysisType(str, Enum):
    FULL_DOCUMENT = "full_document"
    SECTION = "section"

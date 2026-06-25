from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.enums.analysis_type import AnalysisType


class AnalysisCreateRequest(BaseModel):
    document_id: str = Field(..., description="被分析的文档 ID。")
    section_id: str | None = Field(
        default=None, description="小节 ID；仅小节分析时需要。"
    )
    analysis_type: AnalysisType = Field(
        ..., description="分析范围：全文解析或小节解析。"
    )
    language: str = Field(default="zh", description="分析结果输出语言。")
    model_name: str | None = Field(default=None, description="指定使用的 AI 模型名称。")
    prompt_version: str | None = Field(
        default=None, description="指定使用的提示词模板版本。"
    )


class AnalysisResponse(BaseModel):
    id: str = Field(..., description="分析结果 ID。")
    document_id: str = Field(..., description="被分析的文档 ID。")
    section_id: str | None = Field(
        default=None, description="小节 ID（仅小节分析时返回）。"
    )
    analysis_type: AnalysisType = Field(..., description="分析范围。")
    language: str = Field(..., description="分析结果语言。")
    content_markdown: str = Field(..., description="用于展示的 Markdown 内容。")
    content_json: dict | None = Field(
        default=None, description="供程序读取的结构化分析内容。"
    )
    model_name: str | None = Field(default=None, description="生成结果使用的 AI 模型。")
    prompt_version: str | None = Field(default=None, description="提示词模板版本。")
    created_at: datetime = Field(..., description="创建时间。")
    updated_at: datetime = Field(..., description="最后更新时间。")


class TermEntry(BaseModel):
    fr: str = Field(..., description="French technical term")
    zh: str = Field(..., description="Chinese translation")
    explanation: str = Field(..., description="Bilingual explanation")


class SourceRef(BaseModel):
    page: int | None = Field(default=None, description="Source page number")
    title: str | None = Field(default=None, description="Section title")


class AnalysisOutput(BaseModel):
    summary: str = Field(..., description="Brief summary in Simplified Chinese")
    key_concepts: list[str] = Field(
        default_factory=list, description="Key concepts in Chinese"
    )
    terms: list[TermEntry] = Field(
        default_factory=list, description="French-Chinese terminology entries"
    )
    highlights: list[str] = Field(
        default_factory=list, description="Important points in Chinese"
    )
    source_refs: list[SourceRef] = Field(
        default_factory=list, description="Source references"
    )


class SourceCitation(BaseModel):
    id: str = Field(..., description="Citation ID")
    page: int | None = Field(default=None, description="Source page number")
    document_unit_id: str = Field(..., description="Source DocumentUnit ID")
    chunk_id: str | None = Field(default=None, description="Source Chunk ID")
    source_text: str = Field(..., description="Original text supporting the sentence")
    start_char: int = Field(..., ge=0, description="Start character offset in source page text")
    end_char: int = Field(..., ge=0, description="End character offset in source page text")

    @model_validator(mode="after")
    def validate_char_range(self) -> "SourceCitation":
        if self.end_char < self.start_char:
            raise ValueError("end_char must be greater than or equal to start_char")
        return self


class SectionAnalysisSentence(BaseModel):
    id: str = Field(..., description="Sentence ID")
    text: str = Field(..., description="Analysis sentence text")
    citations: list[SourceCitation] = Field(
        default_factory=list,
        description="Sentence-level source citations",
    )


class SourcePage(BaseModel):
    page: int | None = Field(default=None, description="Source page number")
    document_unit_id: str = Field(..., description="Source DocumentUnit ID")
    text: str = Field(..., description="Text-version PDF page content")


class SectionAnalysisOutput(BaseModel):
    section_id: str = Field(..., description="Section ID")
    section_title: str = Field(..., description="Section title")
    status: Literal["draft", "completed"] = Field(..., description="Analysis status")
    sentences: list[SectionAnalysisSentence] = Field(
        default_factory=list,
        description="Sentence-level analysis output",
    )
    source_pages: list[SourcePage] = Field(
        default_factory=list,
        description="Text-version PDF source pages",
    )

    @model_validator(mode="after")
    def validate_completed_sentences_have_citations(self) -> "SectionAnalysisOutput":
        if self.status == "completed":
            uncited_sentence_ids = [
                sentence.id for sentence in self.sentences if not sentence.citations
            ]
            if uncited_sentence_ids:
                raise ValueError(
                    "completed section analysis requires citations for every sentence: "
                    + ", ".join(uncited_sentence_ids)
                )
        return self

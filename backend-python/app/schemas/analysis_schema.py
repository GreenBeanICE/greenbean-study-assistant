from datetime import datetime

from pydantic import BaseModel, Field

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


class SectionAnalysisGenerateRequest(BaseModel):
    language: str = Field(default="zh", description="分析结果输出语言。")
    force_regenerate: bool = Field(
        default=False, description="是否强制重新生成解析。"
    )


class SectionAnalysisResponse(BaseModel):
    id: str = Field(..., description="分析结果 ID。")
    document_id: str = Field(..., description="被分析的文档 ID。")
    section_id: str = Field(..., description="小节 ID。")
    analysis_type: AnalysisType = Field(..., description="分析范围。")
    language: str = Field(..., description="分析结果语言。")
    content_markdown: str = Field(..., description="用于展示的 Markdown 内容。")
    content_json: dict | None = Field(
        default=None, description="供程序读取的结构化分析内容。"
    )
    source_refs: list[SourceRef] = Field(
        default_factory=list, description="来源引用列表。"
    )
    model_name: str | None = Field(default=None, description="生成结果使用的 AI 模型。")
    prompt_version: str | None = Field(default=None, description="提示词模板版本。")
    created_at: datetime = Field(..., description="创建时间。")
    updated_at: datetime = Field(..., description="最后更新时间。")

    @classmethod
    def from_entity(cls, result: "AnalysisResult") -> "SectionAnalysisResponse":
        refs: list[SourceRef] = []
        if result.content_json and isinstance(
            result.content_json.get("source_refs"), list
        ):
            refs = [
                SourceRef.model_validate(item)
                for item in result.content_json["source_refs"]
            ]
        return cls(
            id=result.id,
            document_id=result.document_id,
            section_id=result.section_id or "",
            analysis_type=result.analysis_type,
            language=result.language,
            content_markdown=result.content_markdown,
            content_json=result.content_json,
            source_refs=refs,
            model_name=result.model_name,
            prompt_version=result.prompt_version,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

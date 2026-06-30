# 分析服务，用于组织 AI 结构化分析流程。

from typing import Protocol

from app.agents.analysis_agent import AnalysisAgent
from app.entities.analysis_result import AnalysisResult
from app.enums.analysis_type import AnalysisType
from app.rag.context_builder import SectionContextBuilder
from app.schemas.analysis_schema import SectionAnalysisOutput


# 这是一个工具函数，把 Agent 吐出来的 JSON 变成漂亮的 Markdown 排版
def build_markdown_from_json(analysis_data: dict) -> str:
    """
    将大模型生成的结构化 JSON 转换为前端展示用的中法双语 Markdown 文本。
    """
    md = f"## 🇨🇳 中文总结\n\n{analysis_data.get('summary', '')}\n\n"

    md += "### 💡 核心概念\n\n"
    for concept in analysis_data.get("key_concepts", []):
        md += f"- {concept}\n"

    md += "\n### 📚 中法专业术语对照\n\n"
    for term in analysis_data.get("terms", []):
        md += f"- **{term.get('fr', '')}** ({term.get('zh', '')}): {term.get('explanation', '')}\n"

    md += "\n### 🎯 重点提炼\n\n"
    for highlight in analysis_data.get("highlights", []):
        md += f"- {highlight}\n"

    return md


def build_markdown_from_section_analysis(analysis_data: dict) -> str:
    """将句子级小节解析 JSON 转换为前端展示用 Markdown。"""

    section_title = analysis_data.get("section_title", "小节解析")
    lines = [f"## {section_title}", ""]
    for sentence in analysis_data.get("sentences", []):
        text = sentence.get("text", "").strip()
        if text:
            lines.append(text)
    return "\n\n".join(lines).strip()


class SectionAnalysisAgentProtocol(Protocol):
    async def generate_section_analysis(
        self,
        *,
        section_context,
        language: str,
        model_name: str | None,
        prompt_version: str,
    ) -> dict:
        """生成句子级可溯源小节解析。"""


class AnalysisResultRepositoryProtocol(Protocol):
    def save(self, result: AnalysisResult) -> AnalysisResult:
        """保存分析结果。"""


class SectionAnalysisService:
    """小节解析应用服务：召回上下文、调用 Agent、校验并保存结果。"""

    def __init__(
        self,
        *,
        context_builder: SectionContextBuilder,
        analysis_agent: SectionAnalysisAgentProtocol | None = None,
        analysis_result_repository: AnalysisResultRepositoryProtocol | None = None,
    ) -> None:
        self.context_builder = context_builder
        self.analysis_agent = analysis_agent or AnalysisAgent()
        self.analysis_result_repository = analysis_result_repository

    async def analyze_section(
        self,
        *,
        section_id: str,
        language: str = "zh",
        model_name: str | None = None,
        prompt_version: str = "section-analysis-v1",
    ) -> AnalysisResult:
        section_context = self.context_builder.build_for_section(section_id)
        raw_output = await self.analysis_agent.generate_section_analysis(
            section_context=section_context,
            language=language,
            model_name=model_name,
            prompt_version=prompt_version,
        )
        raw_output = self._with_context_source_pages(raw_output, section_context)
        validated_output = SectionAnalysisOutput.model_validate(raw_output)
        content_json = validated_output.model_dump()
        result = AnalysisResult(
            document_id=section_context.document_id,
            section_id=section_context.section_id,
            analysis_type=AnalysisType.SECTION,
            language=language,
            content_markdown=build_markdown_from_section_analysis(content_json),
            content_json=content_json,
            model_name=model_name,
            prompt_version=prompt_version,
        )
        if self.analysis_result_repository is not None:
            self.analysis_result_repository.save(result)
            repository_session = getattr(self.analysis_result_repository, "session", None)
            if repository_session is not None:
                repository_session.commit()
        return result

    @staticmethod
    def _with_context_source_pages(raw_output: dict, section_context) -> dict:
        if raw_output.get("source_pages"):
            return raw_output
        output = dict(raw_output)
        output["source_pages"] = [
            {
                "page": unit.page_number,
                "document_unit_id": unit.document_unit_id,
                "text": unit.text_content,
            }
            for unit in section_context.units
        ]
        return output


# =========================================
# 模拟 Service 层组装 Entity 的过程
# =========================================
async def process_and_save_analysis(
    document_id: str, section_id: str, document_context: str
):
    # 1. 实例化 Agent
    agent = AnalysisAgent()

    # 2. 让 Agent 去干活，拿到 JSON 字典 (content_json)
    raw_json_dict = await agent.generate_analysis(document_context)

    # 3. 将 JSON 转换为必填的 Markdown (content_markdown)
    markdown_text = build_markdown_from_json(raw_json_dict)

    # 4. 完美组装进你的 AnalysisResult 实体！
    result_entity = AnalysisResult(
        document_id=document_id,
        section_id=section_id,
        analysis_type=AnalysisType.SECTION,
        language="fr-zh",  # 中法双语
        content_markdown=markdown_text,  # 满足必填条件
        content_json=raw_json_dict,  # 直接塞入大模型原始 JSON
        model_name=None,  # 由 provider 决定使用的模型
        prompt_version="v1.0",  # 记录提示词版本
    )

    # 5. TODO: 接下来你就可以把这个 result_entity 存进 SQLite 的 analyses 表里了！
    # await db.save(result_entity)

    return result_entity

# 分析服务占位文件，后续用于组织 AI 结构化分析流程。

from app.agents.analysis_agent import AnalysisAgent
from app.entities.analysis_result import AnalysisResult
from app.enums.analysis_type import AnalysisType


class SectionAnalysisNotFoundError(ValueError):
    def __init__(self, section_id: str) -> None:
        super().__init__(f"Section not found: {section_id}")
        self.section_id = section_id


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


class AnalysisService:
    """章节解析服务，负责加载章节原文、构建上下文、调用解析 Agent。

    第一版仅基于当前章节的 DocumentUnit 原文生成解析，不混入 chat 或已有解析内容。
    """

    def __init__(
        self,
        *,
        section_service,
        analysis_agent: AnalysisAgent | None = None,
        uow_factory=None,
    ) -> None:
        self.section_service = section_service
        self.analysis_agent = analysis_agent or AnalysisAgent()
        self.uow_factory = uow_factory

    def get_section_analysis(self, section_id: str):
        section = self.section_service.get_section_by_id(section_id)
        if section is None:
            raise SectionAnalysisNotFoundError(section_id)

        if self.uow_factory is None:
            return None

        from app.repositories.analysis_result_repository import AnalysisResultRepository

        with self.uow_factory() as uow:
            return AnalysisResultRepository(uow.session).get_by_section_id(section_id)

    async def generate_section_analysis(
        self,
        section_id: str,
        *,
        language: str = "zh",
        force_regenerate: bool = False,
    ) -> AnalysisResult:
        section = self.section_service.get_section_by_id(section_id)
        if section is None:
            raise SectionAnalysisNotFoundError(section_id)

        existing = None
        if not force_regenerate:
            existing = self.get_section_analysis(section_id)
            if existing is not None:
                return existing
        elif self.uow_factory is not None:
            from app.repositories.analysis_result_repository import AnalysisResultRepository

            with self.uow_factory() as uow:
                existing = AnalysisResultRepository(uow.session).get_by_section_id(section_id)

        content = self.section_service.get_section_content(section_id)
        units = [unit for unit in content["units"] if unit.text_content.strip()]
        if not units:
            raise ValueError("资料依据不足：该章节当前没有可用于生成解析的原文")

        document_context = self._build_section_context(section.title, units)
        analysis_data = await self.analysis_agent.generate_analysis(document_context)
        markdown_text = build_markdown_from_json(analysis_data)
        result_kwargs = {
            "document_id": section.document_id,
            "section_id": section.id,
            "analysis_type": AnalysisType.SECTION,
            "language": language,
            "content_markdown": markdown_text,
            "content_json": analysis_data,
            "prompt_version": "section-v1",
        }
        if existing is not None:
            result_kwargs["id"] = existing.id
            result_kwargs["created_at"] = existing.created_at

        result = AnalysisResult(**result_kwargs)

        if self.uow_factory is None:
            return result

        from app.repositories.analysis_result_repository import AnalysisResultRepository

        with self.uow_factory() as uow:
            saved = AnalysisResultRepository(uow.session).save(result)
            uow.commit()
            return saved

    @staticmethod
    def _build_section_context(section_title: str, units) -> str:
        lines: list[str] = [f"章节标题: {section_title}"]
        for unit in units:
            page_desc = (
                f"第 {unit.page_number} 页"
                if unit.page_number is not None
                else f"单元 {unit.sequence_index + 1}"
            )
            lines.append(f"[{page_desc}]\n{unit.text_content}")
        return "\n\n".join(lines)

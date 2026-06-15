# 分析服务占位文件，后续用于组织 AI 结构化分析流程。

from app.entities.analysis_result import AnalysisResult  # 引入你的实体
from app.enums.analysis_type import AnalysisType


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

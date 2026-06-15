import json
import os
from typing import Any, Dict

from openai import AsyncOpenAI

from app.prompts.analysis_prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    ANALYSIS_USER_PROMPT_TPL,
)
from app.schemas.analysis_schema import AnalysisOutput


class AnalysisAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API Key 未配置！请检查环境变量。")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=os.getenv("API_BASE_URL", "https://api.deepseek.com/v1"),
        )
        self.model = os.getenv("LLM_MODEL", "deepseek-chat")

    async def generate_analysis(self, document_context: str) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": ANALYSIS_USER_PROMPT_TPL.substitute(
                            document_context=document_context
                        ),
                    },
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            raw_content = response.choices[0].message.content
            parsed = json.loads(raw_content)

            validated = AnalysisOutput.model_validate(parsed)
            return validated.model_dump()

        except json.JSONDecodeError as e:
            print(f"解析 JSON 失败, 大模型返回的原始内容为: {raw_content}")
            raise RuntimeError("大模型生成的格式不正确，请重试。") from e
        except Exception as e:
            print(f"生成解析时发生错误: {e}")
            raise e

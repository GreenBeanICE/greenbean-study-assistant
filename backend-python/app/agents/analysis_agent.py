# 分析 Agent 占位文件，后续用于编排结构化分析任务。

import json
import os
from typing import Any, Dict

from openai import AsyncOpenAI

from app.prompts.analysis_prompts import ANALYSIS_SYSTEM_PROMPT


class AnalysisAgent:
    def __init__(self, api_key: str = None):
        """
        初始化解析 Agent，优先从参数读取 API Key，否则从环境变量读取。
        """
        # 优先使用外部传入的密钥，否则读取环境变量，杜绝真实密钥硬编码进代码
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API Key 未配置！请检查环境变量。")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=os.getenv(
                "API_BASE_URL",
                "[https://api.deepseek.com/v1](https://api.deepseek.com/v1)",
            ),
        )
        # 文本解析任务更看重逻辑的严谨性，适合使用标准的 chat 模型
        self.model = os.getenv("LLM_MODEL", "deepseek-chat")

    async def generate_analysis(self, document_context: str) -> Dict[str, Any]:
        """
        接收从 RAG 检索出来的原文内容（chunks），调用大模型生成结构化解析。

        :param document_context: 拼接好的原文内容字符串
        :return: 解析后的字典对象（对应 Schema 中的 content_json）
        """
        try:
            # 发起异步大模型 API 调用
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Please analyze the following text from a course material:\n\n{document_context}",
                    },
                ],
                # 调低随机性（temperature），让模型严格聚焦于原文内容，防止产生技术幻觉
                temperature=0.3,
                # 强管控参数：强制大模型锁死输出格式为纯 JSON，配合 Prompt 实现 100% 纯净输出
                response_format={"type": "json_object"},
            )

            # 提取大模型返回的原生文本内容
            raw_content = response.choices[0].message.content

            # 将结构化的 JSON 字符串转换为 Python 字典，方便后续业务层组装成 Entity 并写入 SQLite
            parsed_json = json.loads(raw_content)
            return parsed_json

        except json.JSONDecodeError as e:
            # 针对大模型极端情况下返回格式异常进行防御性捕获，防止后端服务彻底挂掉
            print(f"解析 JSON 失败, 大模型返回的原始内容为: {raw_content}")
            raise RuntimeError("大模型生成的格式不正确，请重试。") from e
        except Exception as e:
            print(f"生成解析时发生错误: {e}")
            raise e

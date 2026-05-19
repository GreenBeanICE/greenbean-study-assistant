# 分析 Agent 占位文件，后续用于编排结构化分析任务。
import json
from openai import OpenAI
from app.schemas.analysis_schema import RoutingDecision
from app.enums.analysis_type import AnalysisType
from app.prompts.analysis_prompts import ROUTER_SYSTEM_PROMPT

class RouterAgent:
    def __init__(self, api_key: str):
        """
        使用 DeepSeek 的 OpenAI 兼容接口初始化客户端。
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        # 使用 DeepSeek 的标准对话模型
        self.model = "deepseek-chat"

    async def route_question(self, user_question: str) -> RoutingDecision:
        """
        分析学生的意图并返回路由决策。
        """
        try:
            # 调用 API 并启用 JSON 结构化输出模式
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Question de l'étudiant : {user_question}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0  # 将温度设为 0 以保证输出结果的稳定性和确定性
            )
            
            # 提取 JSON 结果并通过 Pydantic 进行数据校验
            result_str = completion.choices[0].message.content
            result_dict = json.loads(result_str)
            decision = RoutingDecision(**result_dict)
            
            # US-09：在控制台打印路由结果，方便后续 Debug 调试
            print(f"[LOG AGENT] Question: '{user_question}' -> Route: {decision.route}")
            
            return decision
            
        except Exception as e:
            # 如果出现技术错误（如断网），则安全降级到 COMPREHENSIVE 综合路由
            print(f"[ERREUR AGENT] 路由分发失败，自动降级处理 : {str(e)}")
            return RoutingDecision(
                route=AnalysisType.COMPREHENSIVE,
                reason=f"调用 API 时发生技术错误 : {str(e)}"
            )
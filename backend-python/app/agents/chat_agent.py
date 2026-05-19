# 聊天 Agent 占位文件，后续用于编排继续追问和对话任务。

from openai import OpenAI

from app.agents.classification_agent import (
    RouterAgent,  # 确保文件名和之前的路由 Agent 匹配
)
from app.prompts.chat_prompts import CHAT_SYSTEM_PROMPT
from app.schemas.chat_schema import ChatRequest, ChatResponse


class ChatAgent:
    def __init__(self, api_key: str):
        """
        初始化聊天 Agent 及其所需的依赖。
        """
        # 初始化 DeepSeek 客户端
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = "deepseek-chat"
        # 引入路由 Agent，用于在回答前先判断用户的提问意图
        self.router = RouterAgent(api_key=api_key)

    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        """
        按照 US-10 的工作流，生成对用户问题的回答。
        """
        # 第一步：获取路由决策（判断是结构问题、概念问题还是综合问题）
        route_decision = await self.router.route_question(request.query)
        print(f"[CHAT AGENT] 识别到的意图 : {route_decision.route}")

        # 第二步：模拟获取数据库资料 (RAG 检索 / PageIndex 结构)
        # TODO : 后续需要替换为真实的 SQLite / sqlite-vec 数据库查询代码
        mock_retrieved_context = "Le polymorphisme est un concept fondamental en programmation orientée objet qui permet à des objets de classes différentes d'être traités comme des objets d'une classe commune."

        # 第三步：构建发送给大模型的消息列表
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]

        # 遍历并追加之前的多轮对话历史记录
        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})

        # 将检索到的课件上下文和用户的新问题组合在一起
        final_user_prompt = f"Contexte extrait :\n{mock_retrieved_context}\n\nQuestion de l'étudiant : {request.query}"
        messages.append({"role": "user", "content": final_user_prompt})

        # 第四步：调用大模型生成最终回答
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,  # 设置较低的温度以保证回答的严谨性和准确性
        )

        # 提取大模型的文本并打包成响应模型返回
        answer = completion.choices[0].message.content
        return ChatResponse(answer=answer)

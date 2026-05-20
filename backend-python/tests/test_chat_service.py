# 聊天服务测试占位文件，后续用于验证对话和上下文逻辑。

# tests/test_chat_agent.py
import json

import pytest
from app.agents.chat_agent import ChatAgent
from app.schemas.chat_schema import ChatMessage, ChatRequest


@pytest.mark.asyncio
async def test_chat_tests():
    """
    执行测试以验证 ChatAgent 的多轮对话流程。
    """
    # 从本地的 api_key.json 读取 API Key
    try:
        with open("api_key.json", "r") as f:
            config = json.load(f)
            YOUR_API_KEY = config.get("DEEPSEEK_API_KEY")
    except FileNotFoundError:
        print("请先在根目录创建 api_key.json 并配置 DEEPSEEK_API_KEY！")
        return
    agent = ChatAgent(api_key=YOUR_API_KEY)

    # 创建一个请求，模拟用户携带了一段对话历史进行追问
    request = ChatRequest(
        query="Peux-tu m'expliquer ce concept plus en détail ?",
        history=[
            ChatMessage(
                role="user", content="Qu'est-ce qu'on va étudier aujourd'hui ?"
            ),
            ChatMessage(
                role="assistant",
                content="Aujourd'hui, nous allons étudier le polymorphisme en Java.",
            ),
        ],
    )

    print("========================================")
    print("           开始测试 CHAT AGENT          ")
    print("========================================")

    response = await agent.generate_response(request)

    print(f"用户问题 : {request.query}")
    print(f"-> AI 的回答 :\n{response.answer}")
    print("========================================")

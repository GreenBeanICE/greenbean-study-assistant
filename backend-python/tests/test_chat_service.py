# 聊天服务测试占位文件，后续用于验证对话和上下文逻辑。

# tests/test_chat_agent.py
import asyncio
from app.agents.chat_agent import ChatAgent
from app.schemas.chat_schema import ChatRequest, ChatMessage

async def run_chat_tests():
    """
    执行测试以验证 ChatAgent 的多轮对话流程。
    """
    # !! 请替换为你真实的 API KEY !!
    YOUR_API_KEY = "sk-d3549edfb48842d2ae9fc36a33595248"
    
    agent = ChatAgent(api_key=YOUR_API_KEY)
    
    # 创建一个请求，模拟用户携带了一段对话历史进行追问
    request = ChatRequest(
        query="Peux-tu m'expliquer ce concept plus en détail ?",
        history=[
            ChatMessage(role="user", content="Qu'est-ce qu'on va étudier aujourd'hui ?"),
            ChatMessage(role="assistant", content="Aujourd'hui, nous allons étudier le polymorphisme en Java.")
        ]
    )
    
    print("========================================")
    print("           开始测试 CHAT AGENT          ")
    print("========================================")
    
    response = await agent.generate_response(request)
    
    print(f"用户问题 : {request.query}")
    print(f"-> AI 的回答 :\n{response.answer}")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_chat_tests())

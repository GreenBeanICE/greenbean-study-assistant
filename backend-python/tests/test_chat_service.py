# 聊天服务测试占位文件，后续用于验证对话和上下文逻辑。

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.agents.chat_agent import ChatAgent
from app.schemas.chat_schema import ChatMessage, ChatRequest


# 使用 @patch 装饰器将 OpenAI 类替换为替身（Mock 对象）
@patch("app.agents.chat_agent.OpenAI")
# 如果你的 ChatAgent 内部也初始化了 RouterAgent，同样需要将其 Mock 掉，以避免触发真实的 API 请求
@patch("app.agents.chat_agent.RouterAgent")
@pytest.mark.asyncio
async def test_chat_agent_with_mock(MockRouterAgent, MockOpenAI):
    """
    测试 ChatAgent，使用 Mock 拦截真实的 API 调用。
    """
    # 1. 配置路由替身的假行为（例如，让它始终返回 CONCEPT 意图）
    mock_router_instance = MockRouterAgent.return_value
    mock_router_decision = MagicMock()
    mock_router_decision.route = "CONCEPT"
    # 注意：如果 route_question 是同步函数，这里用 MagicMock 即可；如果是异步函数，则需要使用 AsyncMock
    mock_router_instance.route_question = AsyncMock(return_value=mock_router_decision)

    # 2. 配置 OpenAI 客户端替身的假行为（大模型的“替身演员”）
    mock_openai_instance = MockOpenAI.return_value

    # 创建一个假回复，极力模仿真实 OpenAI API 的数据层级结构
    mock_message = MagicMock()
    mock_message.content = "🇨🇳 中文解析：这是一个Mock测试。\n🇫🇷 Explication en français : C'est un test mock."

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    # 将拼装好的假数据交还给大模型的 create() 方法
    mock_openai_instance.chat.completions.create.return_value = mock_completion

    # 3. 使用假的 API Key 初始化 Agent
    fake_api_key = "sk-fake-key-for-testing-only"
    agent = ChatAgent(api_key=fake_api_key)

    # 4. 创建一个模拟的用户请求，并带上历史记录
    request = ChatRequest(
        query="Explique-moi le mock",
        history=[ChatMessage(role="user", content="Bonjour")],
    )

    # 5. 执行对话生成方法（这一步完全在本地内存中运行，不会消耗任何网络和 API 额度！）
    response = await agent.generate_response(request)

    # 6. 断言（验证）返回的结果是否完全符合我们的假回复预期
    assert "🇨🇳 中文解析：这是一个Mock测试。" in response.answer
    assert "🇫🇷 Explication en français : C'est un test mock." in response.answer

    # 7. （可选）验证 OpenAI 替身的 API 调用方法是否确实被触发过一次，防止代码逻辑漏调大模型
    mock_openai_instance.chat.completions.create.assert_called_once()

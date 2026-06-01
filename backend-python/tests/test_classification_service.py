# test_router.py

from unittest.mock import MagicMock, patch

import pytest
from app.agents.classification_agent import RouterAgent


# 使用 @patch 拦截 classification_agent 里的 OpenAI 调用
@patch("app.agents.classification_agent.OpenAI")
@pytest.mark.asyncio
async def test_classification_tests_with_mock(MockOpenAI):
    """
    执行一系列测试用例来验证 Agent 的路由准确率（Mock 版本）。
    """
    # 1. 配置 OpenAI 替身（大模型的替身演员）
    mock_openai_instance = MockOpenAI.return_value

    # 创建一个假的大模型回复，这里模拟大模型返回一个标准的 JSON 字符串
    # 假设你的 RouterAgent 期望接收这样的 JSON 并转为 RoutingDecision 对象
    mock_message = MagicMock()
    mock_message.content = (
        '{"route": "CONCEPT", "reason": "这是 Mock 测试模拟的判决理由"}'
    )

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    # 将拼装好的假数据交还给大模型的 create() 方法
    mock_openai_instance.chat.completions.create.return_value = mock_completion

    # 2. 直接使用假 API Key 初始化，绝对安全，不需要读取本地 json 文件！
    fake_api_key = "sk-fake-key-for-testing-only"
    agent = RouterAgent(api_key=fake_api_key)

    # 基于 US-09 需求的测试用例列表
    test_cases = [
        "这份课件分成哪几部分？",
        "第 3 页主要讲什么？",
        "clé étrangère 是什么意思？",
        "解释一下 normalisation",
        "数据库设计这一章有哪些重点概念？",
        "Peux-tu m'expliquer ce qu'est un polymorphisme ?",
    ]

    # 3. 循环执行测试用例（全程不联网，瞬间跑完）
    for question in test_cases:
        decision = await agent.route_question(question)

        # 4. 使用 assert 替代原来的 print，让机器自动校验结果
        # 因为我们的替身写死了返回 "CONCEPT"，所以这里的断言一定成立
        assert decision.route == "CONCEPT"
        assert "模拟的判决理由" in decision.reason

    # 5. （进阶校验）确认我们循环了多少次测试用例，替身就应该被调用了多少次
    assert mock_openai_instance.chat.completions.create.call_count == len(test_cases)

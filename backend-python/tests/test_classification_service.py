# test_router.py
import json

import pytest
from app.agents.classification_agent import RouterAgent


@pytest.mark.asyncio
async def test_classification_tests():
    """
    执行一系列测试用例来验证 Agent 的路由准确率。
    """

    # 从本地的 api_key.json 读取 API Key
    try:
        with open("api_key.json", "r") as f:
            config = json.load(f)
            YOUR_API_KEY = config.get("DEEPSEEK_API_KEY")
    except FileNotFoundError:
        print("请先在根目录创建 api_key.json 并配置 DEEPSEEK_API_KEY！")
        return

    agent = RouterAgent(api_key=YOUR_API_KEY)

    # 基于 US-09 需求的测试用例列表
    test_cases = [
        "这份课件分成哪几部分？",
        "第 3 页主要讲什么？",
        "clé étrangère 是什么意思？",
        "解释一下 normalisation",
        "数据库设计这一章有哪些重点概念？",
        "Peux-tu m'expliquer ce qu'est un polymorphisme ?",
    ]

    print("========================================")
    print("         开始测试 AGENT 智能路由        ")
    print("========================================")

    for question in test_cases:
        decision = await agent.route_question(question)
        print(f"用户提问 : {question}")
        print(f"-> 路由方向 : {decision.route}")
        print(f"-> 判决理由 : {decision.reason}")
        print("-" * 40)

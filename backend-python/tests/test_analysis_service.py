# 分析服务测试占位文件，后续用于验证 AI 分析流程。
# test_router.py
import asyncio

from app.agents.analysis_agent import RouterAgent


async def run_debugging_tests():
    """
    执行一系列测试用例来验证 Agent 的路由准确率。
    """

    YOUR_DEEPSEEK_API_KEY = "sk-d3549edfb48842d2ae9fc36a33595248"

    if YOUR_DEEPSEEK_API_KEY.startswith("sk-xxxx"):
        print("运行测试前，请先填入你真实的 DeepSeek API Key。")
        return

    agent = RouterAgent(api_key=YOUR_DEEPSEEK_API_KEY)

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


if __name__ == "__main__":
    # 启动异步事件循环来运行测试
    asyncio.run(run_debugging_tests())

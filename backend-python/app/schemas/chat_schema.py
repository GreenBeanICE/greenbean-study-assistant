# 聊天请求和响应 Schema 占位文件，后续用于定义 Pydantic 数据结构。
# app/schemas/chat_schema.py
from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    """
    表示对话历史中的单条消息。
    """
    # 消息的角色："user"（用户）或 "assistant"（AI 助手）
    role: str
    # 消息的具体内容
    content: str

class ChatRequest(BaseModel):
    """
    前端发送的新问题请求的数据模型。
    """
    # 用户当前提出的问题
    query: str
    # 当前会话的对话历史记录（默认为空列表）
    history: List[ChatMessage] = []
    # 上下文扩展开关（对应 US-10：是否包含小节解析和历史摘要）
    use_extended_context: bool = False

class ChatResponse(BaseModel):
    """
    返回给前端的响应数据模型。
    """
    # AI 生成的最终回答
    answer: str
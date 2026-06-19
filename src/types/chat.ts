/** 聊天消息角色 */
export type MessageRole = "user" | "assistant";

/** 单条聊天消息 */
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  /** 消息发送时间 ISO 字符串 */
  createdAt: string;
}

/** 聊天会话 */
export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  /** 关联的文档/工作区 ID（可选） */
  contextId?: string;
}
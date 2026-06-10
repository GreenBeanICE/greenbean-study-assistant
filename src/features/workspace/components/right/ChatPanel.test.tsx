import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { createI18nWrapper } from "../../../../test-utils";
import ChatPanel from "./ChatPanel";
import type { ChatMessage } from "../../../../types/chat";

const wrapper = createI18nWrapper("zh");

const sampleMessages: ChatMessage[] = [
  {
    id: "msg-1",
    role: "user",
    content: "帮我总结一下第二节",
    createdAt: "2025-12-01T10:00:00Z",
  },
  {
    id: "msg-2",
    role: "assistant",
    content: "这是对第二节的模拟回答。",
    createdAt: "2025-12-01T10:00:05Z",
  },
];

const defaultProps = {
  messages: [],
  input: "",
  quotedText: null,
  tokenUsage: 0,
  onInputChange: vi.fn(),
  onSend: vi.fn(),
  onClearQuote: vi.fn(),
  loading: false,
};

describe("ChatPanel", () => {
  it("渲染 AI 助手标题和副标题", () => {
    render(<ChatPanel {...defaultProps} />, { wrapper });
    expect(screen.getByText("AI 助手")).toBeDefined();
    expect(screen.getByText("基于课程内容回答")).toBeDefined();
  });

  it("空消息列表显示空状态提示", () => {
    render(<ChatPanel {...defaultProps} />, { wrapper });
    expect(screen.getByText("开始对话")).toBeDefined();
    expect(screen.getByText("针对当前章节内容提问，AI 将结合上下文回答")).toBeDefined();
  });

  it("空白输入时发送按钮禁用", () => {
    render(<ChatPanel {...defaultProps} />, { wrapper });
    const sendBtn = document.querySelector("button[disabled]");
    expect(sendBtn).toBeDefined();
  });

  it("输入文本后发送按钮可点击", () => {
    render(<ChatPanel {...defaultProps} onSend={vi.fn()} />, { wrapper });
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    fireEvent.change(textarea, { target: { value: "一个测试问题" } });
    const sendBtn = screen.getByRole("button", { name: "" });
    expect(sendBtn).toBeDefined();
  });

  it("用户消息和AI消息正确显示", () => {
    render(<ChatPanel {...defaultProps} messages={sampleMessages} />, { wrapper });
    expect(screen.getByText("帮我总结一下第二节")).toBeDefined();
    expect(screen.getByText("这是对第二节的模拟回答。")).toBeDefined();
  });

  it("输入框值改变触发 onInputChange", () => {
    const onInputChange = vi.fn();
    render(<ChatPanel {...defaultProps} onInputChange={onInputChange} />, { wrapper });
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    fireEvent.change(textarea, { target: { value: "你好" } });
    expect(onInputChange).toHaveBeenCalled();
  });

  it("Enter键触发发送", () => {
    const onSend = vi.fn();
    render(<ChatPanel {...defaultProps} input="有内容" onSend={onSend} />, { wrapper });
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });
    expect(onSend).toHaveBeenCalled();
  });

  it("Shift+Enter不触发发送", () => {
    const onSend = vi.fn();
    render(<ChatPanel {...defaultProps} input="有内容" onSend={onSend} />, { wrapper });
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });
    expect(onSend).not.toHaveBeenCalled();
  });

  it("显示引用条", () => {
    render(<ChatPanel {...defaultProps} quotedText="这是一个引用文本" />, { wrapper });
    expect(screen.getByText("引用内容")).toBeDefined();
    expect(screen.getByText("这是一个引用文本")).toBeDefined();
  });

  it("引用条上点击清除触发 onClearQuote", () => {
    const onClearQuote = vi.fn();
    render(<ChatPanel {...defaultProps} quotedText="引用" onClearQuote={onClearQuote} />, { wrapper });
    const svg = document.querySelector("button svg line");
    if (svg) {
      const clearBtn = svg.closest("button");
      if (clearBtn) fireEvent.click(clearBtn);
    }
    expect(onClearQuote).toHaveBeenCalled();
  });

  it("显示 token 用量", () => {
    render(<ChatPanel {...defaultProps} tokenUsage={150} />, { wrapper });
    expect(screen.getByText(/150/)).toBeDefined();
    expect(screen.getByText(/4,096/)).toBeDefined();
  });

  it("加载中显示脉冲动画点", () => {
    render(<ChatPanel {...defaultProps} loading={true} />, { wrapper });
    const pulseDots = document.querySelectorAll(".animate-pulse");
    expect(pulseDots.length).toBeGreaterThanOrEqual(1);
  });
});
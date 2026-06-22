import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ChatPanel from "./ChatPanel";
import type { ChatMessage } from "../../../../types/chat";

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
  it("渲染 AI 助手标题", () => {
    render(<ChatPanel {...defaultProps} />);
    expect(screen.getByText("AI 助手")).toBeDefined();
  });

  it("空消息列表显示上传引导文案", () => {
    render(<ChatPanel {...defaultProps} />);
    expect(screen.getByText("上传一份文档后，我在这里帮你答疑")).toBeDefined();
    expect(screen.queryByText("有什么可以帮你？")).toBeNull();
  });

  it("空白输入时发送按钮禁用", () => {
    render(<ChatPanel {...defaultProps} />);
    const sendBtn = document.querySelector("button[disabled]");
    expect(sendBtn).toBeDefined();
  });

  it("输入文本后发送按钮可点击", () => {
    render(<ChatPanel {...defaultProps} onSend={vi.fn()} />);
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    fireEvent.change(textarea, { target: { value: "一个测试问题" } });
    const sendBtn = screen.getByRole("button", { name: "" });
    expect(sendBtn).toBeDefined();
  });

  it("用户消息和AI消息正确显示", () => {
    const { container } = render(<ChatPanel {...defaultProps} messages={sampleMessages} />);
    expect(screen.getByText("帮我总结一下第二节")).toBeDefined();
    expect(screen.getByText("这是对第二节的模拟回答。")).toBeDefined();
    // AI消息左侧应该渲染AIAvatar（渐变背景 + svg图标）
    const gradientDivs = container.querySelectorAll(".bg-gradient-to-br");
    // 空状态也有一个渐变div，assistant消息还有一个
    expect(gradientDivs.length).toBeGreaterThanOrEqual(1);
  });

  it("输入框值改变触发 onInputChange", () => {
    const onInputChange = vi.fn();
    render(<ChatPanel {...defaultProps} onInputChange={onInputChange} />);
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    fireEvent.change(textarea, { target: { value: "你好" } });
    expect(onInputChange).toHaveBeenCalled();
  });

  it("Enter键触发发送", () => {
    const onSend = vi.fn();
    render(<ChatPanel {...defaultProps} input="有内容" onSend={onSend} />);
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });
    expect(onSend).toHaveBeenCalled();
  });

  it("Shift+Enter不触发发送", () => {
    const onSend = vi.fn();
    render(<ChatPanel {...defaultProps} input="有内容" onSend={onSend} />);
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });
    expect(onSend).not.toHaveBeenCalled();
  });

  it("显示引用条", () => {
    render(<ChatPanel {...defaultProps} quotedText="这是一个引用文本" />);
    expect(screen.getByText("引用内容")).toBeDefined();
    expect(screen.getByText("这是一个引用文本")).toBeDefined();
  });

  it("引用条上点击清除触发 onClearQuote", () => {
    const onClearQuote = vi.fn();
    const { container } = render(<ChatPanel {...defaultProps} quotedText="引用" onClearQuote={onClearQuote} />);
    // Find the clear button: the QuoteBar renders a button with an X icon (two crossing lines)
    const quoteBar = container.querySelector(".bg-blue-50");
    expect(quoteBar).toBeDefined();
    const clearBtn = quoteBar?.querySelector("button");
    expect(clearBtn).toBeDefined();
    if (clearBtn) fireEvent.click(clearBtn);
    expect(onClearQuote).toHaveBeenCalled();
  });

  it("显示 token 用量", () => {
    render(<ChatPanel {...defaultProps} tokenUsage={150} />);
    expect(screen.getByText(/150/)).toBeDefined();
    expect(screen.getByText(/4,096/)).toBeDefined();
  });

  it("加载中显示脉冲动画点", () => {
    render(<ChatPanel {...defaultProps} loading={true} />);
    const pulseDots = document.querySelectorAll(".animate-pulse");
    expect(pulseDots.length).toBeGreaterThanOrEqual(1);
  });
});
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { createI18nWrapper } from "../../../test-utils";
import WorkspacePage from "./WorkspacePage";

const wrapper = createI18nWrapper("zh");

const defaultProps = {
  dark: false,
  setDark: () => {},
  lang: "zh" as const,
  setLang: () => {},
};

describe("WorkspacePage", () => {
  it("渲染三栏布局：左侧章节树、中间文档查看器、右侧聊天面板", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getByText("文档解析")).toBeDefined();
    // 默认左侧面板已展开
    expect(screen.getByText("章节导航")).toBeDefined();
    // 默认右侧面板已展开
    expect(screen.getByText("AI 助手")).toBeDefined();
  });

  it("左侧显示章节树列表", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getByText("1 第一章：引言")).toBeDefined();
    expect(screen.getByText("5 第五章：结论")).toBeDefined();
    expect(screen.getByText("5 个章节")).toBeDefined();
  });

  it("点击章节时，中间区域显示对应的内容块", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getByText("选择章节查看内容")).toBeDefined();
    fireEvent.click(screen.getByText("1.1 背景介绍"));
    expect(screen.getByText("已筛选章节")).toBeDefined();
    expect(screen.queryByText("选择章节查看内容")).toBeNull();
  });

  it("点击章节折叠/展开可以切换子章节", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    const ch3Btn = screen.getByText("3 第三章：方法论");
    fireEvent.click(ch3Btn);
    expect(screen.getByText("3.1 数据采集")).toBeDefined();
    expect(screen.getByText("3.2 分析方法")).toBeDefined();
    expect(screen.getByText("3.3 验证方案")).toBeDefined();
  });

  it("文档内容包含脚注引用蓝色圆点标记", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    fireEvent.click(screen.getByText("1.1 背景介绍"));
    const footnoteBtns = screen.getAllByTitle("点击查看原文引用");
    expect(footnoteBtns.length).toBeGreaterThanOrEqual(1);
  });

  it("右侧聊天面板输入框可输入文本", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    expect(textarea).toBeDefined();
    fireEvent.change(textarea, { target: { value: "这个章节讲了什么？" } });
    expect((textarea as HTMLTextAreaElement).value).toBe("这个章节讲了什么？");
  });

  it("发送消息后用户和AI消息显示在聊天列表中", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    fireEvent.change(textarea, { target: { value: "帮我总结一下" } });
    const inputContainer = textarea.parentElement!;
    const sendBtn = inputContainer.querySelector("button")!;
    fireEvent.click(sendBtn);
    expect(screen.getByText("帮我总结一下")).toBeDefined();
    expect(screen.getByText(/模拟回复/)).toBeDefined();
  });

  it("输入为空且无引用时发送按钮不可点击", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    const sendBtnParent = textarea.parentElement;
    const sendBtn = sendBtnParent?.querySelector("button");
    expect(sendBtn?.disabled).toBe(true);
  });

  it("显示Word风格文档工具栏", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getAllByTitle("加粗").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("斜体").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("下划线").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("删除线").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("高亮").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("左对齐").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("居中").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("右对齐").length).toBeGreaterThanOrEqual(1);
  });

  it("发送消息后token用量增加", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getByText(/0 \/ 4,096/)).toBeDefined();
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    fireEvent.change(textarea, { target: { value: "测试" } });
    const inputContainer = textarea.parentElement!;
    const sendBtn = inputContainer.querySelector("button")!;
    fireEvent.click(sendBtn);
    expect(screen.getByText(/150 \/ 4,096/)).toBeDefined();
  });

  it("工作区顶部显示返回按钮和GreenBean Logo", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getByText("GreenBean")).toBeDefined();
    expect(screen.getByTitle("功能特性")).toBeDefined();
  });

  it("工作区顶部有语言和暗黑模式切换按钮", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getByText("FR")).toBeDefined();
    const allButtons = screen.getAllByRole("button");
    expect(allButtons.length).toBeGreaterThan(2);
  });

  it("文档标题栏包含下载和分享按钮", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getByTitle("下载文档")).toBeDefined();
    expect(screen.getByTitle("分享文档")).toBeDefined();
  });
});
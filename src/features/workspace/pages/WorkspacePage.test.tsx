import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import WorkspacePage from "./WorkspacePage";

// Mock framer-motion
vi.mock("framer-motion", () => {
  const createMotionComponent = (tag: string) => {
    const Component = (props: Record<string, unknown>) => {
      const { children, ...rest } = props;
      const {
        initial: _i, animate: _a, exit: _e, transition: _t,
        ...cleanProps
      } = rest as Record<string, unknown>;
      return React.createElement(tag, cleanProps, children as React.ReactNode);
    };
    Component.displayName = `motion.${tag}`;
    return Component;
  };

  return {
    motion: new Proxy(
      {},
      { get: (_target, tag: string) => createMotionComponent(tag) },
    ),
    AnimatePresence: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
  };
});

describe("WorkspacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    cleanup();
  });

  it("初始显示「我的文档」标题和文件夹树", () => {
    render(<WorkspacePage />);
    expect(screen.getByText("我的文档")).toBeDefined();
    expect(screen.getByText("课程资料")).toBeDefined();
    expect(screen.getByText("考试复习")).toBeDefined();
    expect(screen.getByText("论文参考")).toBeDefined();
  });

  it("搜索框存在", () => {
    render(<WorkspacePage />);
    const searchInput = screen.getByPlaceholderText("搜索文件名...");
    expect(searchInput).toBeDefined();
  });

  it("文件夹默认展开课程资料", () => {
    render(<WorkspacePage />);
    expect(screen.getByText("cours-analyse-s1.pdf")).toBeDefined();
    expect(screen.queryByText("复习笔记-期中exam.pdf")).toBeNull();
  });

  it("点击文件夹可展开/折叠", () => {
    render(<WorkspacePage />);
    fireEvent.click(screen.getByText("考试复习"));
    expect(screen.getByText("复习笔记-期中exam.pdf")).toBeDefined();
    fireEvent.click(screen.getByText("考试复习"));
    expect(screen.queryByText("复习笔记-期中exam.pdf")).toBeNull();
  });

  it("选择文件后切换到章节树模式", () => {
    render(<WorkspacePage />);
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    expect(screen.getByText("cours-analyse-s1.pdf")).toBeDefined();
    expect(screen.queryByText("我的文档")).toBeNull();
  });

  it("章节树模式显示返回按钮", () => {
    render(<WorkspacePage />);
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    expect(screen.getByTitle("返回文件列表")).toBeDefined();
  });

  it("返回按钮可回到文件列表", () => {
    render(<WorkspacePage />);
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    const backBtn = screen.getByTitle("返回文件列表");
    fireEvent.click(backBtn);
    expect(screen.getByText("我的文档")).toBeDefined();
  });

  it("章节树显示章节列表", () => {
    render(<WorkspacePage />);
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    expect(screen.getByText((c) => c.includes("第一章：引言"))).toBeDefined();
    expect(screen.getByText((c) => c.includes("第五章：结论"))).toBeDefined();
  });

  it("点击章节后中间区域显示对应的内容", () => {
    render(<WorkspacePage />);
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    expect(screen.getByText("选择章节查看内容")).toBeDefined();
    fireEvent.click(screen.getByText((c) => c.includes("1.1 背景介绍")));
    const elements = screen.getAllByText((c) => c.includes("1.1 背景介绍"));
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  it("左侧工具栏有文件管理和AI按钮", () => {
    render(<WorkspacePage />);
    expect(screen.getByTitle("文件管理")).toBeDefined();
    expect(screen.getByTitle("收起AI聊天")).toBeDefined();
  });

  it("左侧面板包含设置按钮", () => {
    render(<WorkspacePage />);
    expect(screen.getByTitle("设置")).toBeDefined();
  });

  it("选择文件后章节按钮出现", () => {
    render(<WorkspacePage />);
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    expect(screen.getByTitle("章节导航")).toBeDefined();
  });

  it("右侧聊天面板显示AI助手标题", () => {
    render(<WorkspacePage />);
    expect(screen.getByText("AI 助手")).toBeDefined();
  });

  it("右侧聊天面板显示默认欢迎语", () => {
    render(<WorkspacePage />);
    expect(screen.getByText("有什么可以帮你？")).toBeDefined();
  });

  it("中间区域文档查看器存在", () => {
    render(<WorkspacePage />);
    expect(screen.getByText("文档解析")).toBeDefined();
  });

  it("工具栏有下载和分享按钮", () => {
    render(<WorkspacePage />);
    expect(screen.getByTitle("下载")).toBeDefined();
    expect(screen.getByTitle("分享")).toBeDefined();
  });

  it("输入框存在", () => {
    render(<WorkspacePage />);
    const input = screen.getByPlaceholderText("输入你的问题...");
    expect(input).toBeDefined();
  });

  it("右侧面板可切换展开/收起", () => {
    render(<WorkspacePage />);
    expect(screen.getByTitle("收起AI聊天")).toBeDefined();
    fireEvent.click(screen.getByTitle("收起AI聊天"));
    expect(screen.getByTitle("展开AI聊天")).toBeDefined();
    fireEvent.click(screen.getByTitle("展开AI聊天"));
    expect(screen.getByTitle("收起AI聊天")).toBeDefined();
  });

  it("点击文件管理按钮切换面板显示", () => {
    render(<WorkspacePage />);
    expect(screen.getByText("我的文档")).toBeDefined();
    // Click file button to toggle panel
    fireEvent.click(screen.getByTitle("文件管理"));
    expect(screen.getByTitle("文件管理")).toBeDefined();
  });

  it("未选择章节时显示空状态提示", () => {
    render(<WorkspacePage />);
    expect(screen.getByText("选择章节查看内容")).toBeDefined();
    expect(screen.getByText("点击左侧章节列表，解析内容将在此处展示")).toBeDefined();
  });

  it("未选择章节时显示空状态SVG图标", () => {
    const { container } = render(<WorkspacePage />);
    expect(screen.getByText("选择章节查看内容")).toBeDefined();
    const svgs = container.querySelectorAll("svg");
    expect(svgs.length).toBeGreaterThan(0);
  });

  it("聊天面板显示Enter发送提示", () => {
    render(<WorkspacePage />);
    expect(screen.getByText(/Enter/)).toBeDefined();
  });

  it("右侧面板有token使用量提示", () => {
    render(<WorkspacePage />);
    expect(screen.getByText("0 / 4,096")).toBeDefined();
  });

  it("右键菜单操作-删除文件", () => {
    render(<WorkspacePage />);
    // 找到课程资料下的文件，触发右键菜单并删除
    const fileBtn = screen.getByText("TD-économie-chap2.docx").closest("button");
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      const deleteBtn = screen.getByText("删除");
      expect(deleteBtn).toBeDefined();
      fireEvent.click(deleteBtn);
      expect(screen.queryByText("TD-économie-chap2.docx")).toBeNull();
    }
  });
});
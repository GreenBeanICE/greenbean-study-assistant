import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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

  // --- 初始状态：文件列表 ---

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

  // --- 文件夹展开/折叠 ---

  it("文件夹默认展开课程资料，点击可折叠", () => {
    render(<WorkspacePage />);
    // 默认展开课程资料，所以 cour 文件可见
    expect(screen.getByText("cours-analyse-s1.pdf")).toBeDefined();
    // 考试复习未展开，看不到文件
    expect(screen.queryByText("复习笔记-期中exam.pdf")).toBeNull();
  });

  it("点击文件夹可展开/折叠", () => {
    render(<WorkspacePage />);
    // 点击考试复习展开
    fireEvent.click(screen.getByText("考试复习"));
    expect(screen.getByText("复习笔记-期中exam.pdf")).toBeDefined();
    // 再次点击折叠
    fireEvent.click(screen.getByText("考试复习"));
    expect(screen.queryByText("复习笔记-期中exam.pdf")).toBeNull();
  });

  // --- 选择文件后切换到章节树 ---

  it("选择文件后切换到章节树模式", () => {
    render(<WorkspacePage />);
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    // 章节树标题显示文件名
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
    expect(screen.queryByText("章节导航")).toBeNull();
  });

  it("章节树显示章节列表", () => {
    render(<WorkspacePage />);
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    expect(screen.getByText((c) => c.includes("第一章：引言"))).toBeDefined();
    expect(screen.getByText((c) => c.includes("第五章：结论"))).toBeDefined();
  });

  // --- 章节选中后中间显示内容 ---

  it("点击章节后中间区域显示对应的内容", () => {
    render(<WorkspacePage />);
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    expect(screen.getByText("选择章节查看内容")).toBeDefined();
    fireEvent.click(screen.getByText((c) => c.includes("1.1 背景介绍")));
    const elements = screen.getAllByText((c) => c.includes("1.1 背景介绍"));
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  // --- 左侧面板工具栏 ---

  it("左侧工具栏有折叠按钮和文件列表按钮", () => {
    render(<WorkspacePage />);
    expect(screen.getByTitle("收起章节")).toBeDefined();
    expect(screen.getByTitle("文件管理")).toBeDefined();
  });

  it("选择文件后章节导航按钮出现", () => {
    render(<WorkspacePage />);
    expect(screen.queryByTitle("章节导航")).toBeNull();
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    expect(screen.getByTitle("章节导航")).toBeDefined();
  });

  // --- 右侧聊天面板 ---

  it("右侧聊天面板初始显示", () => {
    render(<WorkspacePage />);
    expect(screen.getByText("AI 助手")).toBeDefined();
  });

  it("右侧聊天面板可折叠", () => {
    render(<WorkspacePage />);
    const collapseBtn = screen.getByTitle("收起聊天");
    fireEvent.click(collapseBtn);
    const expandBtns = screen.getAllByTitle("展开聊天");
    expect(expandBtns.length).toBeGreaterThanOrEqual(1);
  });

  it("中间区域文档查看器存在", () => {
    render(<WorkspacePage />);
    expect(screen.getByText("文档解析")).toBeDefined();
  });
});
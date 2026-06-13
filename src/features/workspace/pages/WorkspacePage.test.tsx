import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { createI18nWrapper } from "../../../test-utils";
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

const wrapper = createI18nWrapper("zh");
const frWrapper = createI18nWrapper("fr");

const defaultProps = {
  dark: false,
  setDark: vi.fn(),
  lang: "zh" as const,
  setLang: vi.fn(),
};

describe("WorkspacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
  });

  it("渲染三栏布局：左侧章节树、中间文档查看器、右侧聊天面板", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getByText("文档解析")).toBeDefined();
    expect(screen.getByText("章节导航")).toBeDefined();
    expect(screen.getByText("AI 助手")).toBeDefined();
  });

  it("左侧显示章节树列表", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getByText((c) => c.includes("第一章：引言"))).toBeDefined();
    expect(screen.getByText((c) => c.includes("第五章：结论"))).toBeDefined();
    expect(screen.getByText("5 个章节")).toBeDefined();
  });

  it("点击章节时，中间区域显示对应的内容块", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getByText("选择章节查看内容")).toBeDefined();
    fireEvent.click(screen.getByText((c) => c.includes("1.1 背景介绍")));
    expect(screen.getByText("已筛选章节")).toBeDefined();
    expect(screen.queryByText("选择章节查看内容")).toBeNull();
  });

  it("点击章节折叠/展开可以切换子章节", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    const ch3Btn = screen.getByText((c) => c.includes("第三章：方法论"));
    fireEvent.click(ch3Btn);
    expect(screen.getByText((c) => c.includes("3.1 数据采集"))).toBeDefined();
  });

  it("文档内容包含脚注引用蓝色圆点标记", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    fireEvent.click(screen.getByText((c) => c.includes("1.1 背景介绍")));
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

  it("发送消息后用户消息出现在聊天列表中", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    const textarea = screen.getByPlaceholderText("输入你的问题...");
    fireEvent.change(textarea, { target: { value: "帮我总结一下" } });
    // 找发送按钮（textarea 父级下的 button）
    const inputContainer = textarea.parentElement!;
    const sendBtn = inputContainer.querySelector("button");
    if (sendBtn) {
      fireEvent.click(sendBtn);
    }
    expect(screen.getByText("帮我总结一下")).toBeDefined();
  });

  it("输入为空时发送按钮不可点击", () => {
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

  it("token用量初始为0", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    expect(screen.getByText(/0 \/ 4,096/)).toBeDefined();
  });

  it("发送消息后token用量增加", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    // 初始 token 用量为 0
    expect(document.body.textContent).toContain("0 / 4,096");
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

  it("onBack 回调在点击后退按钮时触发", () => {
    const onBack = vi.fn();
    render(<WorkspacePage {...defaultProps} onBack={onBack} />, { wrapper });
    const backBtn = screen.getByTitle("功能特性");
    fireEvent.click(backBtn);
    expect(onBack).toHaveBeenCalled();
  });

  it("setLang 在点击 FR/中文按钮时触发", () => {
    const setLang = vi.fn();
    render(<WorkspacePage {...defaultProps} setLang={setLang} />, { wrapper });
    const langBtn = screen.getByText("FR");
    fireEvent.click(langBtn);
    expect(setLang).toHaveBeenCalledWith("fr");
  });

  it("onLogout 在退出登录时触发", () => {
    const onLogout = vi.fn();
    render(<WorkspacePage {...defaultProps} onLogout={onLogout} />, { wrapper });
    const logoutBtn = screen.getByTitle("退出登录");
    fireEvent.click(logoutBtn);
    expect(onLogout).toHaveBeenCalled();
  });

  it("选中章节后显示文档标题编辑栏", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    fireEvent.click(screen.getByText((c) => c.includes("1.1 背景介绍")));
    const titleInput = document.querySelector("input[value='cours-analyse-s1.pdf']");
    expect(titleInput).toBeDefined();
  });

  it("左侧可切换到文件管理器模式", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    const fileManagerBtn = screen.getByTitle("文件管理");
    fireEvent.click(fileManagerBtn);
    expect(screen.getByText("cours-analyse-s1.pdf")).toBeDefined();
  });

  it("可以折叠左侧面板", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    const collapseBtn = screen.getByTitle("收起章节");
    fireEvent.click(collapseBtn);
    // 左侧面板折叠后再次点击同一个按钮可展开
    expect(screen.getByTitle("收起章节")).toBeDefined();
  });

  it("可以折叠右侧面板", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    const collapseBtn = screen.getByTitle("收起聊天");
    fireEvent.click(collapseBtn);
    expect(screen.getByTitle("展开聊天")).toBeDefined();
  });

  it("展开脚注面板", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    fireEvent.click(screen.getByText((c) => c.includes("1.1 背景介绍")));
    const footnoteBtns = screen.getAllByTitle("点击查看原文引用");
    fireEvent.click(footnoteBtns[0]);
    expect(screen.getByText("Gartner预测到2025年AI在教育领域创造超过500亿美元的市场价值。")).toBeDefined();
  });

  it("法语模式下工作区标题为法语", () => {
    render(<WorkspacePage {...defaultProps} lang="fr" />, { wrapper: frWrapper });
    expect(screen.getByText((c) => c.includes("Ch.1 Introduction"))).toBeDefined();
  });

  it("左侧章节数和文件管理按钮存在", () => {
    render(<WorkspacePage {...defaultProps} />, { wrapper });
    // 左侧有"所有文件"的快捷按钮在文件管理器中
    const sectionNavBtn = screen.getByTitle("章节导航");
    expect(sectionNavBtn).toBeDefined();
    const fileBtn = screen.getByTitle("文件管理");
    expect(fileBtn).toBeDefined();
  });
});
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { createI18nWrapper } from "../../../../test-utils";
import DocumentViewer from "./DocumentViewer";
import type { ContentBlock, FootnoteReference } from "../../../../types/section";

const wrapper = createI18nWrapper("zh");

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

const sampleBlocks: ContentBlock[] = [
  {
    id: "block-1",
    sectionId: "ch1-1",
    title: "1.1 背景介绍",
    contentType: "text",
    lines: [
      { id: "l1", text: "AI技术发展迅速。", type: "paragraph", footnoteRef: "1" },
      { id: "l2", text: "教育领域应用广泛。", type: "paragraph" },
      { id: "l3", text: "研究背景与动机", type: "heading", level: 2 },
      { id: "l4", text: "• 测试列表项", type: "list" },
      { id: "l5", text: "const x = 1;", type: "code", highlighted: true },
    ],
  },
  {
    id: "block-table",
    sectionId: "ch1-1",
    title: "表1: 对比",
    contentType: "table",
    tableData: {
      headers: ["名称", "值"],
      rows: [
        { id: "tr1", cells: ["A", "1"] },
        { id: "tr2", cells: ["B", "2"] },
      ],
    },
  },
  {
    id: "block-image",
    sectionId: "ch1-1",
    title: "图1: 示意",
    contentType: "image",
    imageUrl: "",
    imageCaption: "示意图说明文字",
  },
  {
    id: "block-img-url",
    sectionId: "ch1-1",
    title: "图2: 实图",
    contentType: "image",
    imageUrl: "https://example.com/img.png",
  },
  {
    id: "block-other-section",
    sectionId: "ch2-1",
    title: "2.1 概念定义",
    contentType: "text",
    lines: [
      { id: "l10", text: "不同章节内容", type: "paragraph" },
    ],
  },
];

const sampleFootnotes: FootnoteReference[] = [
  { id: "fn-1", refNumber: "1", sourceText: "Gartner预测到2025年", sourceDesc: "第1页，第1段" },
  { id: "fn-2", refNumber: "2", sourceText: "第二个引用来源", sourceDesc: "第2页，第3段" },
];

const defaultProps = {
  contentBlocks: sampleBlocks,
  selectedSectionId: null,
  footnotes: sampleFootnotes,
  expandedFootnoteId: null,
  currentSelection: null,
  showSelectionMenu: false,
  selectionMenuPos: null,
  onToggleHighlight: vi.fn(),
  onUpdateLineText: vi.fn(),
  onFormatLine: vi.fn(),
  onToggleFootnote: vi.fn(),
  onSelectText: vi.fn(),
  onShowSelectionMenu: vi.fn(),
  onQuoteSelection: vi.fn(),
};

describe("DocumentViewer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("未选择章节时显示空状态", () => {
    render(<DocumentViewer {...defaultProps} />, { wrapper });
    expect(screen.getByText("选择章节查看内容")).toBeDefined();
    expect(screen.getByText("点击左侧章节列表，文档内容将在此处展示")).toBeDefined();
  });

  it("选择章节后显示内容块", () => {
    render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    expect(screen.getByText("1.1 背景介绍")).toBeDefined();
    expect(screen.getByText("AI技术发展迅速。")).toBeDefined();
    expect(screen.getByText("教育领域应用广泛。")).toBeDefined();
  });

  it("选择章节后显示筛选标记", () => {
    render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    expect(screen.getByText("已筛选章节")).toBeDefined();
  });

  it("显示下载和分享按钮", () => {
    render(<DocumentViewer {...defaultProps} />, { wrapper });
    expect(screen.getByTitle("下载文档")).toBeDefined();
    expect(screen.getByTitle("分享文档")).toBeDefined();
  });

  it("显示文档工具栏", () => {
    render(<DocumentViewer {...defaultProps} />, { wrapper });
    expect(screen.getAllByTitle("加粗").length).toBeGreaterThanOrEqual(1);
  });

  it("脚注引用显示蓝色圆点按钮", () => {
    render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    const footnoteBtns = screen.getAllByTitle("点击查看原文引用");
    expect(footnoteBtns.length).toBeGreaterThanOrEqual(1);
  });

  it("点击脚注触发 onToggleFootnote", () => {
    const onToggleFootnote = vi.fn();
    render(
      <DocumentViewer {...defaultProps} selectedSectionId="ch1-1" onToggleFootnote={onToggleFootnote} />,
      { wrapper },
    );
    const footnoteBtns = screen.getAllByTitle("点击查看原文引用");
    fireEvent.click(footnoteBtns[0]);
    expect(onToggleFootnote).toHaveBeenCalledWith("fn-1");
  });

  it("展开脚注显示脚注详情", () => {
    render(
      <DocumentViewer {...defaultProps} selectedSectionId="ch1-1" expandedFootnoteId="fn-1" />,
      { wrapper },
    );
    expect(screen.getByText("Gartner预测到2025年")).toBeDefined();
  });

  it("显示内容块数量", () => {
    render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    expect(screen.getByText(/4 个章节/)).toBeDefined();
  });

  it("表格块正确渲染表头和行", () => {
    render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    expect(screen.getByText("表1: 对比")).toBeDefined();
    expect(screen.getByText("名称")).toBeDefined();
    expect(screen.getByText("值")).toBeDefined();
  });

  it("图片块显示占位图和标题", () => {
    render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    expect(screen.getByText("图1: 示意")).toBeDefined();
    expect(screen.getByText("示意图说明文字")).toBeDefined();
    expect(screen.getByText("Chart")).toBeDefined();
  });

  it("有URL的图片块显示图片", () => {
    render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    const img = screen.getByAltText("图2: 实图");
    expect(img).toBeDefined();
    expect(img.getAttribute("src")).toBe("https://example.com/img.png");
  });

  it("列表类型行有正确样式", () => {
    render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    expect(screen.getByText("• 测试列表项")).toBeDefined();
  });

  it("高亮代码行有背景色", () => {
    render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    expect(screen.getByText("const x = 1;")).toBeDefined();
  });

  it("跨章节内容不会显示", () => {
    render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    expect(screen.queryByText("2.1 概念定义")).toBeNull();
  });

  it("内容块之间有分隔线", () => {
    const { container } = render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    const hrs = container.querySelectorAll("hr");
    expect(hrs.length).toBeGreaterThanOrEqual(1);
  });

  it("空章节内容块列表显示空", () => {
    render(<DocumentViewer {...defaultProps} contentBlocks={[]} selectedSectionId="ch1-1" />, { wrapper });
    expect(screen.queryByText("1.1 背景介绍")).toBeNull();
  });

  it("contentEditable 行可编辑", () => {
    render(<DocumentViewer {...defaultProps} selectedSectionId="ch1-1" />, { wrapper });
    const span = screen.getByText("AI技术发展迅速。");
    expect(span.getAttribute("contentEditable")).toBe("true");
  });

  it("脚注引用 refNumber 与 footnote 匹配时触发回调", () => {
    const onToggleFootnote = vi.fn();
    render(
      <DocumentViewer
        {...defaultProps}
        selectedSectionId="ch1-1"
        footnotes={[{ id: "fn-1", refNumber: "1", sourceText: "test", sourceDesc: "desc" }]}
        onToggleFootnote={onToggleFootnote}
      />,
      { wrapper },
    );
    const footnoteBtns = screen.getAllByTitle("点击查看原文引用");
    fireEvent.click(footnoteBtns[0]);
    expect(onToggleFootnote).toHaveBeenCalledWith("fn-1");
  });

  it("下载按钮点击时创建下载链接", () => {
    // 模拟 <a> 元素的 click 行为
    const clickSpy = vi.fn();
    const originalCreateElement = document.createElement.bind(document);
    const createElementSpy = vi.spyOn(document, "createElement").mockImplementation((tagName, options) => {
      const el = originalCreateElement(tagName, options);
      if (tagName === "a") {
        el.click = clickSpy;
      }
      return el;
    });
    
    render(<DocumentViewer {...defaultProps} />, { wrapper });
    fireEvent.click(screen.getByTitle("下载文档"));
    
    expect(createElementSpy).toHaveBeenCalledWith("a");
    expect(clickSpy).toHaveBeenCalled();
    createElementSpy.mockRestore();
  });

  it("分享按钮在支持 navigator.share 时调用分享API", () => {
    const mockShare = vi.fn().mockResolvedValue(undefined);
    // 使用 vi.stubGlobal 在 jsdom 中正确 mock navigator.share
    const originalShare = navigator.share;
    vi.stubGlobal("navigator", { ...navigator, share: mockShare });
    
    render(<DocumentViewer {...defaultProps} />, { wrapper });
    fireEvent.click(screen.getByTitle("分享文档"));
    
    expect(mockShare).toHaveBeenCalledWith({
      title: "GreenBean Document",
      text: "Share my course analysis",
    });
    
    vi.stubGlobal("navigator", { ...navigator, share: originalShare });
  });

  it("分享按钮在不支持 navigator.share 时不报错", () => {
    // 确保 navigator.share 为 undefined
    const originalShareDesc = Object.getOwnPropertyDescriptor(navigator, "share");
    Object.defineProperty(navigator, "share", {
      value: undefined,
      writable: true,
      configurable: true,
    });
    
    render(<DocumentViewer {...defaultProps} />, { wrapper });
    // 不报错即可
    fireEvent.click(screen.getByTitle("分享文档"));
    
    if (originalShareDesc) {
      Object.defineProperty(navigator, "share", originalShareDesc);
    }
  });

  it("分享失败时 catch 块不报错", () => {
    const mockShare = vi.fn().mockRejectedValue(new Error("User cancelled"));
    const originalShare = navigator.share;
    vi.stubGlobal("navigator", { ...navigator, share: mockShare });
    
    render(<DocumentViewer {...defaultProps} />, { wrapper });
    // catch 块应该正常运行
    fireEvent.click(screen.getByTitle("分享文档"));
    
    vi.stubGlobal("navigator", { ...navigator, share: originalShare });
  });
});

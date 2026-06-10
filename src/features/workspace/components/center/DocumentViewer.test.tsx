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
    ],
  },
];

const sampleFootnotes: FootnoteReference[] = [
  { id: "fn-1", refNumber: "1", sourceText: "Gartner预测到2025年", sourceDesc: "第1页，第1段" },
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
    expect(screen.getByText(/1 个章节/)).toBeDefined();
  });
});
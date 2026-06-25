import React from "react";
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import SourcePanel from "./SourcePanel";
import type { SourceCitation, SourcePage } from "../../../../types/section";

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get:
        (_target, tag: string) =>
        ({ children, ...props }: { children: React.ReactNode }) =>
          React.createElement(tag, props, children),
    },
  ),
  AnimatePresence: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}));

const sourcePages: SourcePage[] = [
  {
    page: 1,
    documentUnitId: "unit-1",
    text: "人工智能技术取得了飞速发展，深刻改变了教育资料的学习方式。",
  },
  {
    page: 2,
    documentUnitId: "unit-2",
    text: "在教育领域，AI 技术的应用尤为引人注目。",
  },
];

const citations: SourceCitation[] = [
  {
    id: "c1",
    page: 1,
    documentUnitId: "unit-1",
    chunkId: "chunk-1",
    sourceText: "人工智能技术取得了飞速发展",
    startChar: 0,
    endChar: 14,
  },
  {
    id: "c2",
    page: 2,
    documentUnitId: "unit-2",
    chunkId: "chunk-2",
    sourceText: "AI 技术的应用尤为引人注目",
    startChar: 6,
    endChar: 21,
  },
];

describe("SourcePanel", () => {
  it("展示文字版 PDF 源文件并高亮多个来源", () => {
    render(<SourcePanel sourcePages={sourcePages} activeCitations={citations} />);

    expect(screen.getByText("文字版 PDF 来源")).toBeDefined();
    expect(screen.getByText("第 1 页")).toBeDefined();
    expect(screen.getByText("第 2 页")).toBeDefined();
    expect(screen.getByText(/人工智能技术取得了飞速发展/)).toBeDefined();
    expect(screen.getByText(/AI 技术的应用尤为引人注目/)).toBeDefined();

    const highlights = document.querySelectorAll("[data-source-highlight='true']");
    expect(highlights.length).toBe(2);
  });

  it("没有来源时显示空状态", () => {
    render(<SourcePanel sourcePages={[]} activeCitations={[]} />);

    expect(screen.getByText("选择解析文本后右键显示来源")).toBeDefined();
  });
});

import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import SectionTree from "./SectionTree";
import type { SectionNode } from "../../../../types/section";

const sampleSections: SectionNode[] = [
  {
    id: "ch1",
    title: "第一章：引言",
    index: "1",
    expanded: true,
    children: [
      { id: "ch1-1", title: "背景介绍", index: "1.1" },
      { id: "ch1-2", title: "研究意义", index: "1.2" },
    ],
  },
  { id: "ch2", title: "第二章：理论基础", index: "2", expanded: false },
];

describe("SectionTree", () => {
  it("渲染章节列表和标题", () => {
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={() => {}}
        onToggle={() => {}}
      />,
    );
    expect(screen.getByText((content) => content.includes("第一章：引言"))).toBeDefined();
    expect(screen.getByText((content) => content.includes("第二章：理论基础"))).toBeDefined();
    expect(screen.getByText("章节导航")).toBeDefined();
  });

  it("显示章节数量", () => {
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={() => {}}
        onToggle={() => {}}
      />,
    );
    expect(screen.getByText("2 个章节")).toBeDefined();
  });

  it("展开的父章节显示子章节", () => {
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={() => {}}
        onToggle={() => {}}
      />,
    );
    expect(screen.getByText((content) => content.includes("背景介绍"))).toBeDefined();
    expect(screen.getByText((content) => content.includes("研究意义"))).toBeDefined();
  });

  it("未展开的父章节不显示子章节", () => {
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={() => {}}
        onToggle={() => {}}
      />,
    );
    expect(screen.queryByText("Collecte")).toBeNull();
  });

  it("点击章节触发 onSelect", () => {
    const onSelect = vi.fn();
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={onSelect}
        onToggle={() => {}}
      />,
    );
    fireEvent.click(screen.getByText((content) => content.includes("第一章：引言")));
    expect(onSelect).toHaveBeenCalledWith("ch1");
  });

  it("选择中的章节有正确的样式标记", () => {
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId="ch1"
        onSelect={() => {}}
        onToggle={() => {}}
      />,
    );
    const selectedBtn = screen.getByText((content) => content.includes("第一章：引言"));
    expect(selectedBtn.closest("button")?.className).toContain("bg-neutral-200");
  });

  it("空章节列表显示空状态", () => {
    render(
      <SectionTree
        sections={[]}
        selectedSectionId={null}
        onSelect={() => {}}
        onToggle={() => {}}
      />,
    );
    expect(screen.getByText("暂无章节数据")).toBeDefined();
  });
});
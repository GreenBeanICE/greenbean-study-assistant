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
  { id: "ch3", title: "没有索引的节点" },
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
    expect(screen.getByText("3 个章节")).toBeDefined();
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
    expect(screen.queryByText((content) => content.includes("Collecte"))).toBeNull();
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

  /* ===== 新增覆盖 ===== */

  it("onBack 存在时显示返回按钮", () => {
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={() => {}}
        onToggle={() => {}}
        onBack={vi.fn()}
      />,
    );
    expect(screen.getByTitle("返回文件列表")).toBeDefined();
  });

  it("点击返回按钮触发 onBack", () => {
    const onBack = vi.fn();
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={() => {}}
        onToggle={() => {}}
        onBack={onBack}
      />,
    );
    fireEvent.click(screen.getByTitle("返回文件列表"));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("传入自定义 title 显示自定义标题", () => {
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={() => {}}
        onToggle={() => {}}
        title="自定义标题"
      />,
    );
    expect(screen.getByText("自定义标题")).toBeDefined();
  });

  it("点击展开图标触发 onToggle", () => {
    const onToggle = vi.fn();
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={() => {}}
        onToggle={onToggle}
      />,
    );
    // 展开图标是带有 aria-label 的 span
    const expandBtn = screen.getByLabelText("Collapse section");
    fireEvent.click(expandBtn);
    expect(onToggle).toHaveBeenCalledWith("ch1");
  });

  it("空格键触发 onToggle", () => {
    const onToggle = vi.fn();
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={() => {}}
        onToggle={onToggle}
      />,
    );
    const expandBtn = screen.getByLabelText("Collapse section");
    fireEvent.keyDown(expandBtn, { key: " " });
    expect(onToggle).toHaveBeenCalledWith("ch1");
  });

  it("Enter 键触发 onToggle", () => {
    const onToggle = vi.fn();
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={() => {}}
        onToggle={onToggle}
      />,
    );
    const expandBtn = screen.getByLabelText("Collapse section");
    fireEvent.keyDown(expandBtn, { key: "Enter" });
    expect(onToggle).toHaveBeenCalledWith("ch1");
  });

  it("叶子节点不显示展开图标", () => {
    const onSelect = vi.fn();
    const onToggle = vi.fn();
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={onSelect}
        onToggle={onToggle}
      />,
    );
    // ch3 是叶子节点（无 children），展开/折叠图标是不可见的占位 span
    // 叶子节点点击只触发 onSelect，不触发 onToggle
    fireEvent.click(screen.getByText((content) => content.includes("没有索引")));
    expect(onSelect).toHaveBeenCalledWith("ch3");
    expect(onToggle).not.toHaveBeenCalled();
  });

  it("点击展开的父章节同时触发 onSelect 和 onToggle", () => {
    const onSelect = vi.fn();
    const onToggle = vi.fn();
    render(
      <SectionTree
        sections={sampleSections}
        selectedSectionId={null}
        onSelect={onSelect}
        onToggle={onToggle}
      />,
    );
    // 点击 ch1 的行（在按钮上），应同时触发 onSelect 和 onToggle
    fireEvent.click(screen.getByText((content) => content.includes("第一章：引言")));
    expect(onSelect).toHaveBeenCalledWith("ch1");
    expect(onToggle).toHaveBeenCalledWith("ch1");
  });
});

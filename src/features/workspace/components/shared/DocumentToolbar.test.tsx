import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import DocumentToolbar from "./DocumentToolbar";

describe("DocumentToolbar", () => {
  it("渲染所有格式按钮", () => {
    render(<DocumentToolbar selectedLineId={null} onFormat={() => {}} />);
    expect(screen.getAllByTitle("加粗").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("斜体").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("下划线").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("删除线").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("高亮").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("左对齐").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("居中").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("右对齐").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("插入图片").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("插入表格").length).toBeGreaterThanOrEqual(1);
  });

  it("未选中行时编辑按钮禁用", () => {
    render(<DocumentToolbar selectedLineId={null} onFormat={() => {}} />);
    const disabledButtons = document.querySelectorAll("button[disabled]");
    expect(disabledButtons.length).toBeGreaterThan(0);
  });

  it("选中行后按钮可用", () => {
    render(<DocumentToolbar selectedLineId="line-1" onFormat={() => {}} />);
    const enabledButtons = document.querySelectorAll("button:not([disabled])");
    expect(enabledButtons.length).toBeGreaterThan(0);
  });

  it("插入图片和插入表格按钮始终可用", () => {
    render(<DocumentToolbar selectedLineId={null} onFormat={() => {}} />);
    expect(screen.getAllByTitle("插入图片").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByTitle("插入表格").length).toBeGreaterThanOrEqual(1);
  });

  it("点击插入表格按钮触发 onFormat", () => {
    const onFormat = vi.fn();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={onFormat} />);

    const insertTableBtns = screen.getAllByTitle("插入表格");
    fireEvent.mouseDown(insertTableBtns[0]);
    expect(onFormat).toHaveBeenCalledWith("insert-table");
  });

  it("点击插入图片按钮触发 onFormat", () => {
    const onFormat = vi.fn();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={onFormat} />);

    const insertImageBtns = screen.getAllByTitle("插入图片");
    fireEvent.mouseDown(insertImageBtns[0]);
    expect(onFormat).toHaveBeenCalledWith("insert-image");
  });
});
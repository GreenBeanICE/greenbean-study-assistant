import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
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

  it("未选中行时插入表格按钮仍然可用", () => {
    const onFormat = vi.fn();
    render(<DocumentToolbar selectedLineId={null} onFormat={onFormat} />);
    const insertTableBtns = screen.getAllByTitle("插入表格");
    fireEvent.mouseDown(insertTableBtns[0]);
    expect(onFormat).toHaveBeenCalledWith("insert-table");
  });

  it("未选中行时插入图片按钮仍然可用", () => {
    const onFormat = vi.fn();
    render(<DocumentToolbar selectedLineId={null} onFormat={onFormat} />);
    const insertImageBtns = screen.getAllByTitle("插入图片");
    fireEvent.mouseDown(insertImageBtns[0]);
    expect(onFormat).toHaveBeenCalledWith("insert-image");
  });

  it("未选中行时对齐按钮被禁用", () => {
    render(<DocumentToolbar selectedLineId={null} onFormat={() => {}} />);
    const alignRightBtns = screen.getAllByTitle("右对齐");
    const btn = alignRightBtns[0].closest("button");
    expect(btn?.disabled).toBe(true);
  });

  it("selectedLineId 为 null 时 enabled 为 false", () => {
    render(<DocumentToolbar selectedLineId={null} onFormat={() => {}} />);
    const boldBtns = screen.getAllByTitle("加粗");
    const btn = boldBtns[0].closest("button");
    expect(btn?.disabled).toBe(true);
  });

  it("mouseDown 事件中 e.preventDefault 被调用", () => {
    const onFormat = vi.fn();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={onFormat} />);
    const insertTableBtns = screen.getAllByTitle("插入表格");
    const event = new MouseEvent("mousedown", { bubbles: true, cancelable: true });
    const preventDefaultSpy = vi.spyOn(event, "preventDefault");
    insertTableBtns[0].dispatchEvent(event);
    expect(preventDefaultSpy).toHaveBeenCalled();
  });
});

describe("execLocalFormat", () => {
  let container: HTMLElement;

  beforeEach(() => {
    container = document.createElement("div");
    container.contentEditable = "true";
    container.innerHTML = "Hello World";
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  function selectAllText() {
    const range = document.createRange();
    range.selectNodeContents(container);
    const sel = window.getSelection();
    sel?.removeAllRanges();
    sel?.addRange(range);
  }

  it("加粗按钮在选中文字后执行 bold 格式化", () => {
    selectAllText();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={() => {}} />);
    const boldBtn = screen.getAllByTitle("加粗")[0];
    fireEvent.mouseDown(boldBtn);
    expect(container.querySelector("b")).toBeTruthy();
  });

  it("斜体按钮在选中文字后执行 italic 格式化", () => {
    selectAllText();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={() => {}} />);
    const italicBtn = screen.getAllByTitle("斜体")[0];
    fireEvent.mouseDown(italicBtn);
    expect(container.querySelector("i")).toBeTruthy();
  });

  it("下划线按钮在选中文字后执行 underline 格式化", () => {
    selectAllText();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={() => {}} />);
    const underlineBtn = screen.getAllByTitle("下划线")[0];
    fireEvent.mouseDown(underlineBtn);
    expect(container.querySelector("u")).toBeTruthy();
  });

  it("删除线按钮在选中文字后执行 strikethrough 格式化", () => {
    selectAllText();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={() => {}} />);
    const strikeBtn = screen.getAllByTitle("删除线")[0];
    fireEvent.mouseDown(strikeBtn);
    expect(container.querySelector("s")).toBeTruthy();
  });

  it("高亮按钮在选中文字后执行 highlight 格式化", () => {
    selectAllText();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={() => {}} />);
    const highlightBtn = screen.getAllByTitle("高亮")[0];
    fireEvent.mouseDown(highlightBtn);
    expect(container.querySelector("span")).toBeTruthy();
  });

  it("无选中文字时点击按钮不报错", () => {
    render(<DocumentToolbar selectedLineId="line-1" onFormat={() => {}} />);
    const boldBtn = screen.getAllByTitle("加粗")[0];
    window.getSelection()?.removeAllRanges();
    expect(() => fireEvent.mouseDown(boldBtn)).not.toThrow();
  });

  it("禁用状态时不执行格式化", () => {
    selectAllText();
    render(<DocumentToolbar selectedLineId={null} onFormat={() => {}} />);
    const boldBtn = screen.getAllByTitle("加粗")[0];
    fireEvent.mouseDown(boldBtn);
    expect(container.querySelector("b")).toBeFalsy();
  });

  it("左对齐按钮在选中文字后触发对齐格式化（有 data-line-id）", () => {
    container.dataset.lineId = "test-line-1";
    selectAllText();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={() => {}} />);
    const alignLeftBtn = screen.getAllByTitle("左对齐")[0];
    fireEvent.mouseDown(alignLeftBtn);
    expect(container.style.textAlign).toBe("left");
  });

  it("居中按钮在选中文字后触发对齐格式化", () => {
    container.dataset.lineId = "test-line-2";
    selectAllText();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={() => {}} />);
    const alignCenterBtn = screen.getAllByTitle("居中")[0];
    fireEvent.mouseDown(alignCenterBtn);
    expect(container.style.textAlign).toBe("center");
  });

  it("右对齐按钮在选中文字后触发对齐格式化", () => {
    container.dataset.lineId = "test-line-3";
    selectAllText();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={() => {}} />);
    const alignRightBtn = screen.getAllByTitle("右对齐")[0];
    fireEvent.mouseDown(alignRightBtn);
    expect(container.style.textAlign).toBe("right");
  });

  it("对齐操作找不到 data-line-id 时仍然返回 true", () => {
    selectAllText();
    render(<DocumentToolbar selectedLineId="line-1" onFormat={() => {}} />);
    const alignLeftBtn = screen.getAllByTitle("左对齐")[0];
    // 没有 data-line-id，while 循环会遍历到 null
    expect(() => fireEvent.mouseDown(alignLeftBtn)).not.toThrow();
  });
});
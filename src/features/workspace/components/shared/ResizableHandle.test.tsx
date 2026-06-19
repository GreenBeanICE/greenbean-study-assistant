import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import ResizableHandle from "./ResizableHandle";

describe("ResizableHandle", () => {
  it("渲染分隔条", () => {
    const { container } = render(<ResizableHandle onResize={() => {}} />);
    const handle = container.firstChild as HTMLElement;
    expect(handle).toBeDefined();
    expect(handle.className).toContain("cursor-col-resize");
  });

  it("鼠标拖拽触发 onResize 并传递 clientX", () => {
    const onResize = vi.fn();
    const { container } = render(<ResizableHandle onResize={onResize} />);
    const handle = container.firstChild as HTMLElement;

    fireEvent.mouseDown(handle, { clientX: 100 });
    fireEvent.mouseMove(document, { clientX: 150 });
    // should call with delta=50 and clientX=150
    expect(onResize).toHaveBeenCalledWith(50, 150);

    fireEvent.mouseMove(document, { clientX: 180 });
    expect(onResize).toHaveBeenCalledWith(30, 180);
  });

  it("鼠标松开后停止触发 onResize", () => {
    const onResize = vi.fn();
    const { container } = render(<ResizableHandle onResize={onResize} />);
    const handle = container.firstChild as HTMLElement;

    // 按下并移动一次
    fireEvent.mouseDown(handle, { clientX: 100 });
    fireEvent.mouseMove(document, { clientX: 150 });
    expect(onResize).toHaveBeenCalledTimes(1);

    // 松开
    fireEvent.mouseUp(document);
    onResize.mockClear();

    // 松开后移动不应该触发
    fireEvent.mouseMove(document, { clientX: 200 });
    expect(onResize).not.toHaveBeenCalled();
  });

  it("接受 position 参数", () => {
    const { container } = render(<ResizableHandle onResize={() => {}} position="right" />);
    const handle = container.firstChild as HTMLElement;
    expect(handle).toBeDefined();
  });

  it("鼠标松开时触发 onDragStateChange(false)", () => {
    const onDragStateChange = vi.fn();
    const { container } = render(<ResizableHandle onResize={() => {}} onDragStateChange={onDragStateChange} />);
    const handle = container.firstChild as HTMLElement;

    fireEvent.mouseDown(handle, { clientX: 100 });
    expect(onDragStateChange).toHaveBeenCalledWith(true);

    fireEvent.mouseUp(document);
    expect(onDragStateChange).toHaveBeenCalledWith(false);
  });

  it("双击分隔条触发 onDoubleClick", () => {
    const onDoubleClick = vi.fn();
    const { container } = render(<ResizableHandle onResize={() => {}} onDoubleClick={onDoubleClick} />);
    const handle = container.firstChild as HTMLElement;

    fireEvent.doubleClick(handle);
    expect(onDoubleClick).toHaveBeenCalled();
  });
});
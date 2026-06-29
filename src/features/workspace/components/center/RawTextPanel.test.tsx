import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import RawTextPanel from "./RawTextPanel";
import type { DocumentUnit } from "../../../../types/document";

const mockUnits: DocumentUnit[] = [
  { id: "u1", sequence_index: 0, page_number: 1, text_content: "第一页内容" },
  { id: "u2", sequence_index: 1, page_number: 2, text_content: "第二页内容" },
];

describe("RawTextPanel", () => {
  it("renders empty state when units is empty", () => {
    render(<RawTextPanel units={[]} />);
    expect(screen.getByText("暂无原文数据")).toBeDefined();
  });

  it("renders units with page numbers", () => {
    render(<RawTextPanel units={mockUnits} />);
    expect(screen.getByText("第 1 页")).toBeDefined();
    expect(screen.getByText("第一页内容")).toBeDefined();
    expect(screen.getByText("第 2 页")).toBeDefined();
    expect(screen.getByText("第二页内容")).toBeDefined();
  });

  it("highlights selected unit", () => {
    render(<RawTextPanel units={mockUnits} selectedUnitId="u1" />);
    const selectedUnit = screen.getByText("第一页内容").closest("[data-unit-id]");
    expect(selectedUnit?.getAttribute("data-unit-id")).toBe("u1");
  });

  it("calls onUnitClick when unit is clicked", () => {
    const onUnitClick = vi.fn();
    render(<RawTextPanel units={mockUnits} onUnitClick={onUnitClick} />);
    fireEvent.click(screen.getByText("第一页内容"));
    expect(onUnitClick).toHaveBeenCalledWith("u1");
  });

  it("scrolls selected unit into view when selectedUnitId changes", async () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: scrollIntoView,
    });

    const { rerender } = render(<RawTextPanel units={mockUnits} selectedUnitId={null} />);
    rerender(<RawTextPanel units={mockUnits} selectedUnitId="u2" />);

    await waitFor(() => {
      expect(scrollIntoView).toHaveBeenCalled();
    });
  });
});

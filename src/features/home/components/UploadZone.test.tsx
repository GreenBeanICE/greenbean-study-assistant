import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import UploadZone from "./UploadZone";
import { createI18nWrapper } from "../../../test-utils";

describe("UploadZone", () => {
  it("renders upload prompt text in Chinese", () => {
    render(<UploadZone onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    expect(screen.getByText("拖拽文件到此处，或点击上传")).toBeDefined();
  });

  it("renders upload prompt text in French", () => {
    render(<UploadZone onLogin={() => {}} />, {
      wrapper: createI18nWrapper("fr"),
    });
    expect(screen.getByText("Glissez-déposez ou cliquez pour importer")).toBeDefined();
  });

  it("renders supported format tags", () => {
    render(<UploadZone onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    expect(screen.getByText("PDF")).toBeDefined();
    expect(screen.getByText("DOCX")).toBeDefined();
    expect(screen.getByText("PPTX")).toBeDefined();
    expect(screen.getByText(/TXT \/ MD/)).toBeDefined();
    expect(screen.getByText(/JPG \/ PNG \/ WEBP/)).toBeDefined();
  });

  it("renders format description text", () => {
    render(<UploadZone onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    expect(screen.getByText("文档")).toBeDefined();
    expect(screen.getByText("Word")).toBeDefined();
    expect(screen.getByText("PowerPoint")).toBeDefined();
    expect(screen.getByText("纯文本")).toBeDefined();
    expect(screen.getByText("图片 OCR")).toBeDefined();
  });

  it("calls onLogin when clicked", () => {
    const onLogin = vi.fn();
    render(<UploadZone onLogin={onLogin} />, {
      wrapper: createI18nWrapper("zh"),
    });
    const zone = screen.getByText("拖拽文件到此处，或点击上传").closest("[class*='cursor-pointer']")!;
    fireEvent.click(zone);
    expect(onLogin).toHaveBeenCalledTimes(1);
  });

  it("shows file name after drag-and-drop", () => {
    const onLogin = vi.fn();
    const { container } = render(<UploadZone onLogin={onLogin} />, {
      wrapper: createI18nWrapper("zh"),
    });

    const zone = container.querySelector("[class*='cursor-pointer']")!;
    // Simulate drop event
    const file = new File(["dummy"], "macroeconomic.pdf", { type: "application/pdf" });
    fireEvent.drop(zone, {
      dataTransfer: { files: [file] },
    });

    expect(onLogin).toHaveBeenCalledTimes(1);
    // After drop, the displayed text should be the file name
    expect(screen.getByText("macroeconomic.pdf")).toBeDefined();
  });

  it("changes border style on drag over", () => {
    const { container } = render(<UploadZone onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });

    const zone = container.querySelector("[class*='cursor-pointer']")!;
    fireEvent.dragOver(zone);

    // After dragOver the dragging state should add scale class
    expect(zone.className).toContain("scale");
  });
});
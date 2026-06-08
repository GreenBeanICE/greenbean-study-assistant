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

  it("shows file name and calls onLogin after drag-and-drop with file", () => {
    const onLogin = vi.fn();
    const { container } = render(<UploadZone onLogin={onLogin} />, {
      wrapper: createI18nWrapper("zh"),
    });

    const zone = container.querySelector("[class*='cursor-pointer']")!;
    const file = new File(["dummy"], "macroeconomic.pdf", { type: "application/pdf" });
    fireEvent.drop(zone, {
      dataTransfer: { files: [file] },
    });

    expect(onLogin).toHaveBeenCalledTimes(1);
    expect(screen.getByText("macroeconomic.pdf")).toBeDefined();
  });

  it("does not call onLogin on drop without file", () => {
    const onLogin = vi.fn();
    const { container } = render(<UploadZone onLogin={onLogin} />, {
      wrapper: createI18nWrapper("zh"),
    });

    const zone = container.querySelector("[class*='cursor-pointer']")!;
    fireEvent.drop(zone, {
      dataTransfer: { files: [] },
    });

    expect(onLogin).not.toHaveBeenCalled();
  });

  it("changes border style on drag over and resets on drag leave", () => {
    const { container } = render(<UploadZone onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });

    const zone = container.querySelector("[class*='cursor-pointer']")!;

    fireEvent.dragOver(zone);
    expect(zone.className).toContain("scale");

    fireEvent.dragLeave(zone);
    // After drag leave, the dragging state resets to false
    // The zone should no longer have the scale class or the dragging border
    expect(zone.className).not.toContain("border-black dark:border-white");
  });

  it("handles file change via input", () => {
    const onLogin = vi.fn();
    const { container } = render(<UploadZone onLogin={onLogin} />, {
      wrapper: createI18nWrapper("zh"),
    });

    const input = container.querySelector("input[type='file']")!;
    const file = new File(["content"], "test.pptx", { type: "application/vnd.openxmlformats-officedocument.presentationml.presentation" });

    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText("test.pptx")).toBeDefined();
  });

  it("handles file change via input with no file", () => {
    const onLogin = vi.fn();
    const { container } = render(<UploadZone onLogin={onLogin} />, {
      wrapper: createI18nWrapper("zh"),
    });

    const input = container.querySelector("input[type='file']")!;
    // Change with no files selected
    fireEvent.change(input, { target: { files: [] } });

    // Prompt text should still be visible (no file name set)
    expect(screen.getByText("拖拽文件到此处，或点击上传")).toBeDefined();
  });
});
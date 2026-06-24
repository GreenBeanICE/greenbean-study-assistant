import { describe, expect, it, vi } from "vitest";
import { createFileId, formatFileSize, getFileType, DEFAULT_FOLDERS } from "./workspaceFiles";

describe("workspaceFiles", () => {
  it.each([
    ["lecture.pdf", "PDF"],
    ["notes.doc", "DOC"],
    ["notes.docx", "DOC"],
    ["slides.ppt", "PPT"],
    ["slides.pptx", "PPT"],
    ["scan.jpeg", "IMG"],
    ["scan.jpg", "IMG"],
    ["scan.png", "IMG"],
    ["scan.webp", "IMG"],
    ["readme.md", "MD"],
    ["plain.txt", "TXT"],
    ["unknown.csv", "TXT"],
  ] as const)("maps %s to %s", (fileName, expectedType) => {
    expect(getFileType(fileName)).toBe(expectedType);
  });

  it("formats bytes as MB", () => {
    expect(formatFileSize(2 * 1024 * 1024)).toBe("2.0 MB");
  });

  it("creates file ids with f_ prefix", () => {
    const getRandomValues = vi.spyOn(crypto, "getRandomValues").mockImplementation((array) => {
      (array as Uint32Array)[0] = 123456;
      return array;
    });

    expect(createFileId()).toBe("f_2n9c");
    getRandomValues.mockRestore();
  });

  it("exports the default workspace folders", () => {
    expect(DEFAULT_FOLDERS).toEqual([
      { key: "course", label: "课程资料" },
      { key: "exam", label: "考试复习" },
      { key: "thesis", label: "论文参考" },
    ]);
  });
});

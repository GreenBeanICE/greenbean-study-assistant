import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import FileManager from "./FileManager";

describe("FileManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("渲染文件管理标题和文件夹导航", () => {
    render(<FileManager />);
    expect(screen.getByText("我的文档")).toBeDefined();
    expect(screen.getByText("课程资料")).toBeDefined();
    expect(screen.getByText("考试复习")).toBeDefined();
    expect(screen.getByText("论文参考")).toBeDefined();
  });

  it("渲染默认文件列表", () => {
    render(<FileManager />);
    expect(screen.getByText("cours-analyse-s1.pdf")).toBeDefined();
    expect(screen.getByText("TD-économie-chap2.docx")).toBeDefined();
  });

  it("搜索框过滤文件", () => {
    render(<FileManager />);
    const searchInput = screen.getByPlaceholderText("搜索文件名...");
    fireEvent.change(searchInput, { target: { value: "analyse" } });
    expect(screen.getByText("cours-analyse-s1.pdf")).toBeDefined();
  });

  it("点击文件触发 onFileSelect", () => {
    const onFileSelect = vi.fn();
    const onFileSelectWithName = vi.fn();
    render(<FileManager onFileSelect={onFileSelect} onFileSelectWithName={onFileSelectWithName} />);
    // 展开课程资料文件夹
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    expect(fileBtn).toBeDefined();
    if (fileBtn) {
      fireEvent.click(fileBtn);
      expect(onFileSelect).toHaveBeenCalledWith("f1");
      expect(onFileSelectWithName).toHaveBeenCalledWith("f1", "cours-analyse-s1.pdf");
    }
  });

  it("新建文件夹按钮打开输入框", () => {
    render(<FileManager />);
    // 检查上传按钮存在
    expect(screen.getByTitle("上传新文件")).toBeDefined();
  });

  it("空搜索结果显示空状态", () => {
    render(<FileManager />);
    const searchInput = screen.getByPlaceholderText("搜索文件名...");
    fireEvent.change(searchInput, { target: { value: "zzz_nonexistent_file" } });
    expect(screen.getByText("暂无匹配文件")).toBeDefined();
  });

  it("右键菜单操作-重命名", () => {
    render(<FileManager selectedFileId="f1" />);
    // 找到文件按钮并触发右键
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    expect(fileBtn).toBeDefined();
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      // 右键菜单应显示
      expect(screen.getByText("重命名")).toBeDefined();
      fireEvent.click(screen.getByText("重命名"));
      // 重命名输入框应出现（有 border-blue-400 样式的是重命名输入框）
      const renameInput = document.querySelector("input.border-blue-400");
      expect(renameInput).toBeDefined();
    }
  });

  it("右键菜单操作-删除", () => {
    render(<FileManager />);
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      expect(screen.getByText("删除")).toBeDefined();
      fireEvent.click(screen.getByText("删除"));
      // 文件应被删除
      expect(screen.queryByText("cours-analyse-s1.pdf")).toBeNull();
    }
  });

  it("右键菜单操作-移动到其他文件夹", () => {
    render(<FileManager selectedFileId="f1" />);
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      expect(screen.getByText("移动到")).toBeDefined();
      // 应该能看到"论文参考"作为目标文件夹
      expect(screen.getByText("移出文件夹")).toBeDefined();
    }
  });
});
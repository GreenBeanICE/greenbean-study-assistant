import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import FileManager from "./FileManager";

describe("FileManager", () => {
  it("渲染文件管理标题和文件夹导航", () => {
    render(<FileManager />);
    expect(screen.getByText("我的文档")).toBeDefined();
    expect(screen.getByText("课程资料")).toBeDefined();
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
    fireEvent.change(searchInput, { target: { value: "cours" } });
    expect(screen.getByText("cours-analyse-s1.pdf")).toBeDefined();
    expect(screen.queryByText("bibliographie.pdf")).toBeNull();
  });

  it("点击文件触发 onFileSelect", () => {
    const onFileSelect = vi.fn();
    render(<FileManager onFileSelect={onFileSelect} />);
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    expect(onFileSelect).toHaveBeenCalledWith("f1");
  });

  it("新建文件夹按钮打开输入框", () => {
    render(<FileManager />);
    const addBtn = screen.getByTitle("上传新文件");
    fireEvent.click(addBtn);
  });

  it("空搜索结果显示空状态", () => {
    render(<FileManager />);
    const searchInput = screen.getByPlaceholderText("搜索文件名...");
    fireEvent.change(searchInput, { target: { value: "不存在的文件名称" } });
    expect(screen.getByText("暂无匹配文件")).toBeDefined();
  });
});
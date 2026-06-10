import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { createI18nWrapper } from "../../../../test-utils";
import FileManager from "./FileManager";

const wrapper = createI18nWrapper("zh");

describe("FileManager", () => {
  it("渲染文件管理标题和文件夹导航", () => {
    render(<FileManager />, { wrapper });
    expect(screen.getByText("文件管理")).toBeDefined();
    expect(screen.getByText("所有文件")).toBeDefined();
    expect(screen.getByText("AI")).toBeDefined();
    expect(screen.getByText("法律")).toBeDefined();
    expect(screen.getByText("论文参考")).toBeDefined();
  });

  it("渲染默认文件列表", () => {
    render(<FileManager />, { wrapper });
    expect(screen.getByText("cours-analyse-s1.pdf")).toBeDefined();
    expect(screen.getByText("TD-économie-chap2.docx")).toBeDefined();
  });

  it("搜索框过滤文件", () => {
    render(<FileManager />, { wrapper });
    const searchInput = screen.getByPlaceholderText("搜索文件名...");
    fireEvent.change(searchInput, { target: { value: "cours" } });
    expect(screen.getByText("cours-analyse-s1.pdf")).toBeDefined();
    expect(screen.queryByText("bibliographie.pdf")).toBeNull();
  });

  it("点击文件夹分类过滤文件", () => {
    render(<FileManager />, { wrapper });
    // 点击"法律"文件夹
    const examBtn = screen.getByText("法律");
    fireEvent.click(examBtn);
    expect(screen.getByText((content) => content.includes("exam.pdf"))).toBeDefined();
    expect(screen.queryByText("cours-analyse-s1.pdf")).toBeNull();
  });

  it("点击文件触发 onFileSelect", () => {
    const onFileSelect = vi.fn();
    render(<FileManager onFileSelect={onFileSelect} />, { wrapper });
    fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
    expect(onFileSelect).toHaveBeenCalledWith("f1");
  });

  it("新建文件夹按钮打开输入框", () => {
    render(<FileManager />, { wrapper });
    const addBtn = screen.getByTitle("新建文件夹");
    fireEvent.click(addBtn);
    expect(screen.getByPlaceholderText("输入文件夹名称...")).toBeDefined();
  });

  it("空搜索结果显示空状态", () => {
    render(<FileManager />, { wrapper });
    const searchInput = screen.getByPlaceholderText("搜索文件名...");
    fireEvent.change(searchInput, { target: { value: "不存在的文件名称" } });
    expect(screen.getByText("暂无匹配文件")).toBeDefined();
  });
});
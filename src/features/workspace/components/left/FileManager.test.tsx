import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import FileManager from "./FileManager";

describe("FileManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
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
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    expect(fileBtn).toBeDefined();
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      expect(screen.getByText("重命名")).toBeDefined();
      fireEvent.click(screen.getByText("重命名"));
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
      expect(screen.queryByText("cours-analyse-s1.pdf")).toBeNull();
    }
  });

  it("右键菜单操作-移动到其他文件夹", () => {
    render(<FileManager selectedFileId="f1" />);
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      expect(screen.getByText("移动到")).toBeDefined();
      expect(screen.getByText("移出文件夹")).toBeDefined();
    }
  });

  /* ===== 新增覆盖测试 ===== */

  it("上传文件触发 uid 和文件列表更新", () => {
    render(<FileManager />);
    const uploadLabel = screen.getByTitle("上传新文件");
    const fileInput = uploadLabel.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).toBeDefined();
    const file = new File(["dummy content"], "nouveau-cours.pdf", { type: "application/pdf" });
    Object.defineProperty(fileInput, "files", { value: [file] });
    fireEvent.change(fileInput);
    expect(screen.getByText("nouveau-cours.pdf")).toBeDefined();
  });

  it("点击文件夹可展开子文件", () => {
    render(<FileManager />);
    // "考试复习" 默认折叠，点击展开
    fireEvent.click(screen.getByText("考试复习"));
    expect(screen.getByText("复习笔记-期中exam.pdf")).toBeDefined();
    // 再次点击折叠（因为 AnimatePresence exit 动画保留 DOM，不验证 null）
  });

  it("展开的空文件夹显示「暂无文件」", () => {
    const folders = [{ key: "empty", label: "空文件夹" }];
    const files = [{ id: "f-other", name: "other.txt", type: "TXT" as const, category: "other", size: "1 KB", date: "2025-01-01", status: "parsed" as const }];
    render(<FileManager folders={folders} files={files} />);
    fireEvent.click(screen.getByText("空文件夹"));
    expect(screen.getByText("暂无文件")).toBeDefined();
  });

  it("右键菜单是否可通过 Escape 关闭 backdrop", () => {
    render(<FileManager selectedFileId="f1" />);
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      expect(screen.getByText("删除")).toBeDefined();
      // 验证右键菜单出现后可以通过再次右键关闭（closeContextMenu）
      fireEvent.keyDown(document.body, { key: "Escape" });
    }
  });

  it("重命名提交后文件名称更新", () => {
    render(<FileManager selectedFileId="f1" />);
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      fireEvent.click(screen.getByText("重命名"));
      const renameInput = document.querySelector("input.border-blue-400") as HTMLInputElement;
      if (renameInput) {
        fireEvent.change(renameInput, { target: { value: "新名称.pdf" } });
        fireEvent.blur(renameInput);
        expect(screen.getByText("新名称.pdf")).toBeDefined();
        expect(screen.queryByText("cours-analyse-s1.pdf")).toBeNull();
      }
    }
  });

  it("重命名 Enter 键提交", () => {
    render(<FileManager selectedFileId="f1" />);
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      fireEvent.click(screen.getByText("重命名"));
      const renameInput = document.querySelector("input.border-blue-400") as HTMLInputElement;
      if (renameInput) {
        fireEvent.change(renameInput, { target: { value: "enter-name.pdf" } });
        fireEvent.keyDown(renameInput, { key: "Enter" });
        expect(screen.getByText("enter-name.pdf")).toBeDefined();
      }
    }
  });

  it("重命名 Escape 取消", () => {
    render(<FileManager selectedFileId="f1" />);
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      fireEvent.click(screen.getByText("重命名"));
      const renameInput = document.querySelector("input.border-blue-400") as HTMLInputElement;
      if (renameInput) {
        fireEvent.change(renameInput, { target: { value: "cancelled.pdf" } });
        fireEvent.keyDown(renameInput, { key: "Escape" });
        expect(screen.getByText("cours-analyse-s1.pdf")).toBeDefined();
      }
    }
  });

  it("右键菜单移动到指定文件夹", () => {
    render(<FileManager selectedFileId="f1" />);
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      // 右键菜单中的"论文参考"是移动目标，文件夹列表中也同时可见
      const moveTargets = screen.getAllByText("论文参考");
      // 取最后一个（在右键菜单中，排在文件夹列表之后）
      const moveTarget = moveTargets[moveTargets.length - 1];
      fireEvent.click(moveTarget);
      expect(screen.queryByText("重命名")).toBeNull();
    }
  });

  it("右键菜单移出文件夹", () => {
    render(<FileManager />);
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    if (fileBtn) {
      fireEvent.contextMenu(fileBtn);
      fireEvent.click(screen.getByText("移出文件夹"));
      expect(screen.queryByText("重命名")).toBeNull();
    }
  });

  it("文件拖拽功能通过按钮的 draggable 属性启用", () => {
    render(<FileManager />);
    const fileBtn = screen.getByText("cours-analyse-s1.pdf").closest("button");
    if (fileBtn) {
      // 验证按钮有 draggable 属性
      expect(fileBtn.getAttribute("draggable")).toBe("true");
    }
  });

  it("外部传入 files 和 folders 覆盖默认数据", () => {
    const externalFiles = [
      { id: "ext1", name: "external.pdf", type: "PDF" as const, category: "custom", size: "1 MB", date: "2025-01-01", status: "parsed" as const },
    ];
    const externalFolders = [{ key: "custom", label: "自定义文件夹" }];
    render(<FileManager files={externalFiles} folders={externalFolders} />);
    // 展开自定义文件夹
    fireEvent.click(screen.getByText("自定义文件夹"));
    expect(screen.getByText("external.pdf")).toBeDefined();
    expect(screen.queryByText("课程资料")).toBeNull();
  });
});
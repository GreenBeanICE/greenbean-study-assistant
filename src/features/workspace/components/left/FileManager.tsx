/**
 * 文件管理面板 — 文件夹树结构，支持上传、右键重命名/删除/移动
 */

import { useState, useMemo, useCallback, useRef } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import type { FileItem, FileManagerProps, FileType } from "../../type";
import { createFileId, DEFAULT_FOLDERS, formatFileSize, getFileType } from "../../workspaceFiles";

/* ------------------------------------------------------------------ */
/*  类型定义                                                           */
/* ------------------------------------------------------------------ */

export type { FileItem, Folder } from "../../type";

/* ------------------------------------------------------------------ */
/*  类型颜色映射                                                       */
/* ------------------------------------------------------------------ */

const TYPE_STYLES: Record<FileType, { bg: string; text: string; label: string }> = {
  PDF: { bg: "#fee2e2", text: "#dc2626", label: "PDF" },
  DOC: { bg: "#dbeafe", text: "#2563eb", label: "DOC" },
  PPT: { bg: "#fef3c7", text: "#d97706", label: "PPT" },
  IMG: { bg: "#fce7f3", text: "#db2777", label: "IMG" },
  TXT: { bg: "#f0fdf4", text: "#16a34a", label: "TXT" },
  MD:  { bg: "#f5f3ff", text: "#7c3aed", label: "MD" },
};

/* ------------------------------------------------------------------ */
/*  文件管理器组件                                                     */
/* ------------------------------------------------------------------ */

export default function FileManager({
  files: externalFiles,
  folders: externalFolders,
  selectedFileId,
  onUpload,
  onFileSelect,
  onFileSelectWithName,
  onDeleteFile,
  onRenameFile,
  onMoveFile,
}: FileManagerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(["course"]));
  const [internalFiles, setInternalFiles] = useState<FileItem[]>([]);

  // 右键菜单状态
  const [contextMenu, setContextMenu] = useState<{ fileId: string; x: number; y: number } | null>(null);
  // 重命名状态
  const [renaming, setRenaming] = useState<{ fileId: string; name: string } | null>(null);
  const renameInputRef = useRef<HTMLInputElement>(null);

  const folders = externalFolders ?? DEFAULT_FOLDERS;
  const allFiles = externalFiles ?? internalFiles;

  /** 切换文件夹展开/折叠 */
  const toggleFolder = useCallback((key: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  /** 搜索过滤后的文件 */
  const searchFiltered = useMemo(() => {
    if (!searchQuery.trim()) return null;
    return allFiles.filter((f) =>
      f.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [allFiles, searchQuery]);

  /** 某个文件夹的文件列表 */
  const getFolderFiles = useCallback((key: string): FileItem[] => {
    return allFiles
      .filter((f) => f.category === key)
      .sort((a, b) => {
        if (a.status === "parsed" && b.status !== "parsed") return -1;
        if (a.status !== "parsed" && b.status === "parsed") return 1;
        return a.name.localeCompare(b.name);
      });
  }, [allFiles]);

  const searchResults = searchFiltered;
  const isSearching = searchQuery.trim().length > 0;

  /** 获取文件所属文件夹 */
  const getFileCategory = useCallback((fileId: string) => {
    const file = allFiles.find((f) => f.id === fileId);
    return file?.category;
  }, [allFiles]);

  /** 上传文件 */
  const handleUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const newFile: FileItem = {
        id: createFileId(),
        name: file.name,
        type: getFileType(file.name),
        category: "",
        size: formatFileSize(file.size),
        date: new Date().toISOString().split('T')[0],
        status: "pending",
      };
      onUpload?.(file);
      if (!externalFiles) {
        setInternalFiles((prev) => [newFile, ...prev]);
      }
    }
    (e.target as HTMLInputElement).value = "";
  }, []);

  /** 右键打开菜单 */
  const handleContextMenu = useCallback((e: React.MouseEvent, fileId: string) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({ fileId, x: e.clientX, y: e.clientY });
  }, []);

  /** 关闭右键菜单 */
  const closeContextMenu = useCallback(() => setContextMenu(null), []);

  /** 删除文件 */
  const handleDelete = useCallback((fileId: string) => {
    onDeleteFile?.(fileId);
    if (!externalFiles) {
      setInternalFiles((prev) => prev.filter((f) => f.id !== fileId));
    }
    closeContextMenu();
  }, [closeContextMenu, externalFiles, onDeleteFile]);

  /** 开始重命名 */
  const handleStartRename = useCallback((fileId: string) => {
    const file = allFiles.find((f) => f.id === fileId);
    if (file) {
      setRenaming({ fileId, name: file.name });
      closeContextMenu();
      setTimeout(() => renameInputRef.current?.focus(), 50);
    }
  }, [allFiles, closeContextMenu]);

  /** 提交重命名 */
  const handleRenameSubmit = useCallback(() => {
    if (renaming && renaming.name.trim()) {
      onRenameFile?.(renaming.fileId, renaming.name.trim());
      if (!externalFiles) {
        setInternalFiles((prev) => prev.map((f) =>
          f.id === renaming.fileId ? { ...f, name: renaming.name.trim() } : f
        ));
      }
    }
    setRenaming(null);
  }, [externalFiles, onRenameFile, renaming]);

  /** 移动文件到指定文件夹 */
  const handleMove = useCallback((fileId: string, toCategory: string) => {
    onMoveFile?.(fileId, toCategory);
    if (!externalFiles) {
      setInternalFiles((prev) => prev.map((f) =>
        f.id === fileId ? { ...f, category: toCategory } : f
      ));
    }
    closeContextMenu();
  }, [closeContextMenu, externalFiles, onMoveFile]);

  /** 点击文件 */
  const handleFileClick = useCallback((fileId: string, fileName: string) => {
    onFileSelect?.(fileId);
    onFileSelectWithName?.(fileId, fileName);
  }, [onFileSelect, onFileSelectWithName]);

  /** 渲染单个文件按钮（共用） */
  const renderFileButton = (file: FileItem, compact = false) => {
    const isSelected = selectedFileId === file.id;
    const style = TYPE_STYLES[file.type];
    const isRenaming = renaming?.fileId === file.id;

    return (
      <div key={file.id} className="relative group/file">
        {isRenaming ? (
          <div className="flex items-center gap-1 px-2 py-1">
            <input
              ref={renameInputRef}
              value={renaming.name}
              onChange={(e) => setRenaming((prev) => prev ? { ...prev, name: e.target.value } : null)}
              onKeyDown={(e) => { if (e.key === "Enter") handleRenameSubmit(); if (e.key === "Escape") setRenaming(null); }}
              onBlur={handleRenameSubmit}
              className="flex-1 h-6 px-1.5 rounded bg-black/5 text-[11px] text-neutral-700 outline-none border border-blue-400"
            />
          </div>
        ) : (
          <button
            onClick={() => handleFileClick(file.id, file.name)}
            onContextMenu={(e) => handleContextMenu(e, file.id)}
            className={`cursor-pointer w-full flex items-center gap-2 text-left transition-all duration-200 ${
              compact
                ? "px-2 py-1.5 rounded-lg"
                : "px-2.5 py-2 rounded-xl"
            } ${
              isSelected ? "bg-black text-white shadow-sm" : "text-neutral-600 hover:bg-black/5"
            }`}
          >
            <div className={`flex-shrink-0 rounded-md flex items-center justify-center font-bold ${
              compact ? "w-6 h-6 text-[7px]" : "w-7 h-7 rounded-lg text-[7px]"
            }`} style={{ backgroundColor: style.bg, color: style.text }}>
              {style.label}
            </div>
            <span className={`font-medium truncate ${compact ? "text-[11px]" : "text-xs"} ${isSelected ? "text-white" : "text-neutral-700"}`}>
              {file.name}
            </span>
            {!compact && (
              <span className={`ml-auto text-[9px] ${isSelected ? "text-white/60" : "text-neutral-400"}`}>{file.size}</span>
            )}
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* 标题 + 上传按钮 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-black/5">
        <h2 className="text-sm font-semibold text-neutral-700 tracking-tight">我的文档</h2>
        <label className="cursor-pointer w-6 h-6 rounded-md flex items-center justify-center hover:bg-black/10 text-neutral-400 transition" title="上传新文件">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <input type="file" accept=".pdf,.docx,.pptx,.txt,.md,.png,.jpg,.webp" className="hidden" onChange={handleUpload} />
        </label>
      </div>

      {/* 搜索框 */}
      <div className="px-3 py-2 border-b border-black/5">
        <div className="relative">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
            className="absolute left-2.5 top-1/2 -translate-y-1/2 text-neutral-400">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索文件名..."
            className="w-full h-7 pl-7 pr-2 rounded-lg bg-black/5 text-[11px] text-neutral-600 placeholder-neutral-400 outline-none border-none focus:ring-1 focus:ring-blue-500/30 transition-all"
          />
        </div>
      </div>

      {/* 文件夹树 */}
      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5 scrollbar-hide" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
        {/* 搜索模式 */}
        {isSearching && searchResults && (
          <>
            {searchResults.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <p className="text-xs text-neutral-400">暂无匹配文件</p>
              </div>
            ) : (
              <div className="space-y-0.5">
                {searchResults.map((file) => renderFileButton(file, false))}
              </div>
            )}
          </>
        )}

        {/* 非搜索模式：文件夹树 */}
        {!isSearching && (
          <div className="space-y-0.5">
            {/* 无所属文件夹的文件（不上传） */}
            {(() => {
              const uncategorized = allFiles.filter((f) => !f.category || f.category === "");
              if (uncategorized.length === 0) return null;
              return (
                <div className="ml-3 space-y-0.5 mb-1">
                  {uncategorized.map((file) => renderFileButton(file, true))}
                </div>
              );
            })()}
            {folders.map((folder) => {
              const folderFiles = getFolderFiles(folder.key);
              const isExpanded = expandedFolders.has(folder.key);
              return (
                <div key={folder.key}>
                  <button
                    onClick={() => toggleFolder(folder.key)}
                    className="cursor-pointer w-full flex items-center gap-2 px-2.5 py-2 rounded-xl text-left text-neutral-600 hover:bg-black/5 transition-all duration-200">
                    <motion.span animate={{ rotate: isExpanded ? 90 : 0 }} transition={{ duration: 0.15 }}
                      className="flex-shrink-0 w-4 h-4 flex items-center justify-center">
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6" /></svg>
                    </motion.span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="flex-shrink-0 text-amber-500">
                      <path d="M2 6a2 2 0 0 1 2-2h5l2 2h9a2 2 0 0 1 2 2v1H2V6zM2 10h20v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-8z" />
                    </svg>
                    <span className="text-xs font-medium text-neutral-700 truncate flex-1">{folder.label}</span>
                    <span className="text-[10px] text-neutral-400">{folderFiles.length}</span>
                  </button>
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}
                        className="overflow-hidden">
                        <div className="ml-5 border-l border-black/10 pl-2 space-y-0.5">
                          {folderFiles.map((file) => renderFileButton(file, true))}
                          {folderFiles.length === 0 && (
                            <p className="text-[10px] text-neutral-400 px-2 py-1">暂无文件</p>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 右键菜单 - 使用 Portal 确保在整个页面最上层 */}
      {contextMenu && createPortal(
        <>
          <div className="fixed inset-0 z-[9999]" onClick={closeContextMenu} onKeyDown={(e) => { if (e.key === 'Escape') closeContextMenu(); }} tabIndex={0} role="button" aria-label="关闭菜单" />
          <div className="fixed z-[10000] bg-white rounded-xl shadow-xl border border-black/10 py-1 min-w-[160px]"
            style={{ left: contextMenu.x, top: contextMenu.y }}>
            <button onClick={() => handleStartRename(contextMenu.fileId)}
              className="cursor-pointer w-full flex items-center gap-2 px-3 py-2 text-xs text-neutral-700 hover:bg-black/5 transition">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
              重命名
            </button>
            <div className="border-t border-black/5 my-1" />
            <div className="px-3 py-1 text-[10px] font-medium text-neutral-400">移动到</div>
            {folders.filter((f) => f.key !== (getFileCategory(contextMenu.fileId) || "")).map((f) => (
              <button key={f.key} onClick={() => handleMove(contextMenu.fileId, f.key)}
                className="cursor-pointer w-full flex items-center gap-2 px-3 py-2 text-xs text-neutral-700 hover:bg-black/5 transition">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-amber-500">
                  <path d="M2 6a2 2 0 0 1 2-2h5l2 2h9a2 2 0 0 1 2 2v1H2V6zM2 10h20v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-8z" />
                </svg>
                {f.label}
              </button>
            ))}
            <button onClick={() => handleMove(contextMenu.fileId, "")}
              className="cursor-pointer w-full flex items-center gap-2 px-3 py-2 text-xs text-neutral-700 hover:bg-black/5 transition">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></svg>
              移出文件夹
            </button>
            <div className="border-t border-black/5 my-1" />
            <button onClick={() => handleDelete(contextMenu.fileId)}
              className="cursor-pointer w-full flex items-center gap-2 px-3 py-2 text-xs text-red-600 hover:bg-red-50 transition">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>
              删除
            </button>
          </div>
        </>,
        document.body
      )}
    </div>
  );
}

/**
 * 文件管理面板 — 支持用户自定义文件夹、添加/移出文件、上传时选择文件夹
 *
 * 所有文件夹（包括预设的 AI、法律、论文参考）完全同质，用户可删除任意一个。
 */

import { useState, useMemo, useCallback, useEffect } from "react";
import { useI18n } from "../../../../lib/i18n";

/* ------------------------------------------------------------------ */
/*  类型定义                                                           */
/* ------------------------------------------------------------------ */

export type FileType = "PDF" | "DOC" | "PPT" | "IMG" | "TXT" | "MD";
export type FileStatus = "parsed" | "parsing" | "pending";

export interface FileItem {
  id: string;
  name: string;
  type: FileType;
  category: string;
  size: string;
  date: string;
  status: FileStatus;
}

export interface Folder {
  key: string;
  label: string;
}

export interface FileManagerProps {
  files?: FileItem[];
  folders?: Folder[];
  selectedFileId?: string | null;
  onFileSelect?: (fileId: string) => void;
  onAddFolder?: (label: string) => void;
  onRemoveFolder?: (key: string) => void;
  onMoveFile?: (fileId: string, toCategory: string) => void;
  onRemoveFile?: (fileId: string) => void;
  onFilesChange?: (files: FileItem[]) => void;
  onFoldersChange?: (folders: Folder[]) => void;
  /** 预览模式下默认打开右键菜单的文件 ID，用于首页截图场景 */
  showContextMenuFor?: string | null;
}

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
/*  默认数据                                                           */
/* ------------------------------------------------------------------ */

export const DEFAULT_FOLDERS: Folder[] = [
  { key: "all", label: "所有文件" },
  { key: "course", label: "AI" },
  { key: "exam", label: "法律" },
  { key: "thesis", label: "论文参考" },
];

export function getDefaultFiles(lang: string): FileItem[] {
  const zh = lang === "zh";
  return [
    { id: "f1", name: "cours-analyse-s1.pdf", type: "PDF", category: "course", size: "12.4 MB", date: "2025-09-15", status: "parsed" },
    { id: "f2", name: "TD-économie-chap2.docx", type: "DOC", category: "course", size: "3.2 MB", date: "2025-10-02", status: "parsed" },
    { id: "f3", name: "cours-droit-commercial.pptx", type: "PPT", category: "course", size: "45.8 MB", date: "2025-10-10", status: "parsing" },
    { id: "f4", name: "cours-maths-tableau.webp", type: "IMG", category: "course", size: "2.1 MB", date: "2025-10-15", status: "pending" },
    { id: "f5", name: zh ? "复习笔记-期中exam.pdf" : "révision-exam.pdf", type: "PDF", category: "exam", size: "8.5 MB", date: "2025-11-01", status: "parsed" },
    { id: "f6", name: zh ? "论文-引言部分.docx" : "mémoire-intro.docx", type: "DOC", category: "thesis", size: "1.8 MB", date: "2025-11-10", status: "parsed" },
    { id: "f7", name: zh ? "参考文献列表.pdf" : "bibliographie.pdf", type: "PDF", category: "thesis", size: "5.3 MB", date: "2025-11-15", status: "pending" },
    { id: "f8", name: "TD-statistiques.pptx", type: "PPT", category: "course", size: "28.6 MB", date: "2025-11-20", status: "parsing" },
  ];
}

/** 生成唯一标识，用于文件夹 key */
function uid(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return `f_${crypto.randomUUID().slice(0, 8)}`;
  }
  // 使用 CSPRNG 生成随机值（兼容不支持 crypto.randomUUID 的环境）
  if (typeof crypto !== "undefined" && crypto.getRandomValues) {
    const array = new Uint32Array(1);
    crypto.getRandomValues(array);
    return `f_${array[0].toString(36).slice(0, 7)}`;
  }
  return `f_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

/* ------------------------------------------------------------------ */
/*  文件管理器组件                                                     */
/* ------------------------------------------------------------------ */

export default function FileManager({
  files: externalFiles,
  folders: externalFolders,
  selectedFileId,
  onFileSelect,
  onAddFolder,
  onRemoveFolder,
  onMoveFile,
  onRemoveFile,
  showContextMenuFor,
}: FileManagerProps) {
  const { t, lang } = useI18n();

  const [internalFolders, setInternalFolders] = useState<Folder[]>(DEFAULT_FOLDERS);
  const [internalFiles, setInternalFiles] = useState<FileItem[]>(() => getDefaultFiles(lang));

  const folders = externalFolders ?? internalFolders;
  const allFiles = externalFiles ?? internalFiles;

  const setFolders = useCallback(
    (f: Folder[] | ((prev: Folder[]) => Folder[])) => {
      if (externalFolders) return;
      const next = typeof f === "function" ? f(internalFolders) : f;
      setInternalFolders(next);
    },
    [externalFolders, internalFolders],
  );

  const setFiles = useCallback(
    (f: FileItem[] | ((prev: FileItem[]) => FileItem[])) => {
      if (externalFiles) return;
      const next = typeof f === "function" ? f(internalFiles) : f;
      setInternalFiles(next);
    },
    [externalFiles, internalFiles],
  );

  const [activeCategory, setActiveCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showAddFolder, setShowAddFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [contextMenu, setContextMenu] = useState<{ fileId: string; x: number; y: number } | null>(
    showContextMenuFor ? { fileId: showContextMenuFor, x: 240, y: 180 } : null,
  );

  const filteredFiles = useMemo(
    () =>
      allFiles.filter((f) => {
        if (activeCategory !== "all" && f.category !== activeCategory) return false;
        if (searchQuery.trim() && !f.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
        return true;
      }),
    [allFiles, activeCategory, searchQuery],
  );

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { all: allFiles.length };
    for (const f of allFiles) {
      counts[f.category] = (counts[f.category] || 0) + 1;
    }
    return counts;
  }, [allFiles]);

  // 所有子文件夹（不含 "all"），包括预设的和用户新建的，完全同质
  const subFolders = useMemo(() => folders.filter((f) => f.key !== "all"), [folders]);

  const handleAddFolder = () => {
    const name = newFolderName.trim();
    if (!name) return;
    if (folders.some((f) => f.label === name)) return;
    const newFolder: Folder = { key: uid(), label: name };
    const next = [...folders, newFolder];
    setFolders(next);
    onAddFolder?.(name);
    setNewFolderName("");
    setShowAddFolder(false);
  };

  const handleRemoveFolder = (key: string) => {
    const next = folders.filter((f) => f.key !== key);
    const nextFiles = allFiles.map((f) => (f.category === key ? { ...f, category: "all" } : f));
    setFolders(next);
    setFiles(nextFiles);
    onRemoveFolder?.(key);
    if (activeCategory === key) setActiveCategory("all");
  };

  const handleMoveFile = (fileId: string, toCategory: string) => {
    const next = allFiles.map((f) => (f.id === fileId ? { ...f, category: toCategory } : f));
    setFiles(next);
    onMoveFile?.(fileId, toCategory);
  };

  const handleRemoveFile = (fileId: string) => {
    const next = allFiles.filter((f) => f.id !== fileId);
    setFiles(next);
    onRemoveFile?.(fileId);
  };

  const handleContextMenu = (e: React.MouseEvent, fileId: string) => {
    e.preventDefault();
    setContextMenu({ fileId, x: e.clientX, y: e.clientY });
  };

  const folderIcon = (key: string) => {
    if (key === "all") return "M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2z";
    return "M2 6a2 2 0 0 1 2-2h5l2 2h9a2 2 0 0 1 2 2v1H2V6zM2 10h20v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-8z";
  };

  return (
    <div className="flex flex-col h-full">
      {/* 标题栏 + 新建文件夹按钮 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-black/5 dark:border-white/10">
        <h2 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 tracking-tight">{t("wsFileTitle")}</h2>
        <button
          onClick={() => setShowAddFolder(!showAddFolder)}
          className="cursor-pointer w-6 h-6 rounded-md flex items-center justify-center hover:bg-black/10 dark:hover:bg-white/10 text-neutral-400 dark:text-neutral-500 transition"
          title={t("wsFileAddFolder")}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </button>
      </div>

      {/* 新建文件夹输入栏 */}
      {showAddFolder && (
        <div className="px-3 py-2 border-b border-black/5 dark:border-white/10 bg-white/30 dark:bg-white/[0.02]">
          <div className="flex gap-1.5">
            <input
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAddFolder();
                if (e.key === "Escape") { setShowAddFolder(false); setNewFolderName(""); }
              }}
              placeholder={t("wsFileFolderName")}
              autoFocus
              className="flex-1 h-7 px-2 rounded-lg bg-black/5 dark:bg-white/10 text-[11px] text-neutral-600 dark:text-neutral-300 placeholder-neutral-400 outline-none border-none focus:ring-1 focus:ring-blue-500/30 transition-all"
            />
            <button onClick={handleAddFolder} className="cursor-pointer w-7 h-7 rounded-lg bg-black text-white dark:bg-white dark:text-black flex items-center justify-center text-[10px] font-medium hover:opacity-85 transition">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12" /></svg>
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* 左侧文件夹导航 */}
        <div className="w-[90px] flex-shrink-0 border-r border-black/5 dark:border-white/10 bg-white/40 dark:bg-white/[0.02]">
          {/* "所有文件" 固定置顶 */}
          <button
            onClick={() => setActiveCategory("all")}
            className={`cursor-pointer w-full flex flex-col items-center gap-0.5 px-2 py-2.5 text-center transition-all duration-200 ${
              activeCategory === "all"
                ? "bg-black/5 dark:bg-white/10 text-neutral-800 dark:text-neutral-200"
                : "text-neutral-500 dark:text-neutral-400 hover:bg-black/5 dark:hover:bg-white/10"
            }`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
              <path d={folderIcon("all")} />
            </svg>
            <span className="text-[9px] font-medium leading-tight">{t("wsFileAll")}</span>
            <span className="text-[8px] text-neutral-400 dark:text-neutral-500">{categoryCounts["all"] || 0}</span>
          </button>

          {/* 分隔线 */}
          <div className="mx-3 my-1.5 border-t border-black/10 dark:border-white/10" />

          {/* 所有子文件夹 — 完全同质，全部可删除 */}
          {subFolders.map((folder) => (
            <div key={folder.key} className="relative group">
              <button
                onClick={() => setActiveCategory(folder.key)}
                className={`cursor-pointer w-full flex flex-col items-center gap-0.5 px-2 py-2.5 text-center transition-all duration-200 ${
                  activeCategory === folder.key
                    ? "bg-black/5 dark:bg-white/10 text-neutral-800 dark:text-neutral-200"
                    : "text-neutral-500 dark:text-neutral-400 hover:bg-black/5 dark:hover:bg-white/10"
                }`}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
                  <path d={folderIcon(folder.key)} />
                </svg>
                <span className="text-[9px] font-medium leading-tight truncate max-w-[70px]">{folder.label}</span>
                <span className="text-[8px] text-neutral-400 dark:text-neutral-500">{categoryCounts[folder.key] || 0}</span>
              </button>

              {/* 所有子文件夹均可删除 */}
              <button
                onClick={(e) => { e.stopPropagation(); handleRemoveFolder(folder.key); }}
                className="cursor-pointer absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-neutral-200 dark:bg-neutral-700 flex items-center justify-center opacity-0 group-hover:opacity-100 hover:bg-red-300 dark:hover:bg-red-600 transition-all"
                title={t("wsFileRemoveFolder")}
              >
                <svg width="6" height="6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              </button>
            </div>
          ))}
        </div>

        {/* 右侧文件列表 */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="px-3 py-2 border-b border-black/5 dark:border-white/10">
            <div className="relative">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                className="absolute left-2.5 top-1/2 -translate-y-1/2 text-neutral-400 dark:text-neutral-500">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t("wsFileSearch")}
                className="w-full h-7 pl-7 pr-2 rounded-lg bg-black/5 dark:bg-white/10 text-[11px] text-neutral-600 dark:text-neutral-300 placeholder-neutral-400 dark:placeholder-neutral-500 outline-none border-none focus:ring-1 focus:ring-blue-500/30 transition-all"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-2 py-1.5 space-y-0.5 scrollbar-hide" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
            {filteredFiles.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <div className="w-10 h-10 rounded-xl bg-black/5 dark:bg-white/10 flex items-center justify-center mb-2">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" className="text-neutral-400 dark:text-neutral-500">
                    <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                    <polyline points="13 2 13 9 20 9" />
                  </svg>
                </div>
                <p className="text-xs text-neutral-400 dark:text-neutral-500">{t("wsFileEmpty")}</p>
              </div>
            ) : (
              filteredFiles.map((file) => {
                const isSelected = selectedFileId === file.id;
                const style = TYPE_STYLES[file.type];

                return (
                  <div key={file.id} className="relative">
                    <button
                      onClick={() => onFileSelect?.(file.id)}
                      onContextMenu={(e) => handleContextMenu(e, file.id)}
                      className={`cursor-pointer w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left transition-all duration-200 ${
                        isSelected
                          ? "bg-black text-white dark:bg-white dark:text-black shadow-md"
                          : "text-neutral-600 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/10"
                      }`}
                    >
                      <div
                        className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-[8px] font-bold"
                        style={{ backgroundColor: style.bg, color: style.text }}
                      >
                        {style.label}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-xs font-medium truncate ${isSelected ? "text-white" : "text-neutral-700 dark:text-neutral-300"}`}>
                          {file.name}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className={`text-[10px] ${isSelected ? "text-white/70" : "text-neutral-400 dark:text-neutral-500"}`}>{file.date}</span>
                          <span className={`text-[10px] ${isSelected ? "text-white/50" : "text-neutral-400 dark:text-neutral-500"}`}>{file.size}</span>
                        </div>
                      </div>
                    </button>

                    {contextMenu?.fileId === file.id && (
                      <>
                        <div className="fixed inset-0 z-40" onClick={() => setContextMenu(null)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setContextMenu(null); }} tabIndex={0} role="button" aria-label="Close context menu" />
                        <div className="fixed z-50 bg-white dark:bg-neutral-800 rounded-xl shadow-xl border border-black/10 dark:border-white/10 py-1 min-w-[160px]" style={{ left: contextMenu.x, top: contextMenu.y }}>
                          <div className="px-3 py-1.5 text-[10px] font-medium text-neutral-400 dark:text-neutral-500 uppercase tracking-wider">{t("wsFileMoveTo")}</div>
                          {folders.filter((f) => f.key !== file.category).map((f) => (
                            <button key={f.key} onClick={() => { handleMoveFile(file.id, f.key); setContextMenu(null); }}
                              className="cursor-pointer w-full flex items-center gap-2 px-3 py-2 text-xs text-neutral-700 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/10 transition">
                              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d={folderIcon(f.key)} /></svg>
                              {f.label}
                            </button>
                          ))}
                          <div className="border-t border-black/5 dark:border-white/10 my-1" />
                          <button onClick={() => { handleRemoveFile(file.id); setContextMenu(null); }}
                            className="cursor-pointer w-full flex items-center gap-2 px-3 py-2 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                              <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>
                            {t("wsFileRemove")}
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
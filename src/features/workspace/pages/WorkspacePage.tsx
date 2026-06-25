import { useReducer, useCallback, useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import SectionTree from "../components/left/SectionTree";
import FileManager from "../components/left/FileManager";
import DocumentViewer from "../components/center/DocumentViewer";
import ChatPanel from "../components/right/ChatPanel";
import ResizableHandle from "../components/shared/ResizableHandle";
import type { FileItem, WorkspaceState, WorkspaceAction, WorkspacePageProps } from "../type";
import { createFileId, DEFAULT_FOLDERS, formatFileSize, getFileType } from "../workspaceFiles";
import type { SectionNode, ContentLine, ContentBlock } from "../../../types/section";
import type { ChatMessage } from "../../../types/chat";
import { uploadDocument, getDocumentDetail } from "../../document/api/documentApi";
import { unitsToContentBlocks, UPLOADED_CONTENT_SECTION_ID } from "../../document/unitsToContentBlocks";

export function workspaceReducer(state: WorkspaceState, action: WorkspaceAction): WorkspaceState {
  switch (action.type) {
    case "SELECT_SECTION": return { ...state, selectedSectionId: action.sectionId };
    case "TOGGLE_SECTION_EXPAND": {
      const toggleExpand = (nodes: SectionNode[]): SectionNode[] => nodes.map((n) => {
        if (n.id === action.sectionId) return { ...n, expanded: !(n.expanded ?? true) };
        if (n.children) return { ...n, children: toggleExpand(n.children) };
        return n;
      });
      return { ...state, sections: toggleExpand(state.sections) };
    }
    case "TOGGLE_HIGHLIGHT":
      return { ...state, contentBlocks: state.contentBlocks.map((b) => b.id !== action.blockId || !b.lines ? b : { ...b, lines: b.lines.map((l: ContentLine) => l.id === action.lineId ? { ...l, highlighted: !l.highlighted } : l) }) };
    case "UPDATE_LINE_TEXT":
      return { ...state, contentBlocks: state.contentBlocks.map((b) => b.id !== action.blockId || !b.lines ? b : { ...b, lines: b.lines.map((l: ContentLine) => l.id === action.lineId ? { ...l, text: action.text } : l) }) };
    case "FORMAT_LINE":
      return { ...state, contentBlocks: state.contentBlocks.map((b) => {
        if (b.id !== action.blockId || !b.lines) return b;
        return { ...b, lines: b.lines.map((l: ContentLine) => {
          if (l.id !== action.lineId) return l;
          const f = action.format;
          if (f === "bold") return { ...l, bold: !l.bold };
          if (f === "italic") return { ...l, italic: !l.italic };
          if (f === "underline") return { ...l, underline: !l.underline };
          if (f === "strikethrough") return { ...l, strikethrough: !l.strikethrough };
          if (f === "highlight") return { ...l, highlighted: !l.highlighted };
          if (f === "align-left") return { ...l, align: l.align === "left" ? undefined : "left" };
          if (f === "align-center") return { ...l, align: l.align === "center" ? undefined : "center" };
          if (f === "align-right") return { ...l, align: l.align === "right" ? undefined : "right" };
          return l;
        }) as ContentLine[] };
      })};
    case "SET_LANG_DATA": return { ...state, sections: action.sections, contentBlocks: action.contentBlocks };
    case "TOGGLE_FOOTNOTE": return { ...state, expandedFootnoteId: state.expandedFootnoteId === action.footnoteId ? null : action.footnoteId };
    case "SET_SELECTION": return { ...state, currentSelection: action.selection };
    case "SHOW_SELECTION_MENU": return { ...state, showSelectionMenu: action.show, selectionMenuPos: action.pos ?? null };
    case "QUOTE_SELECTION": return { ...state, quotedText: state.currentSelection?.text ?? null, showSelectionMenu: false, currentSelection: null, selectionMenuPos: null };
    case "CLEAR_QUOTE": return { ...state, quotedText: null };
    case "SET_CHAT_INPUT": return { ...state, chatInput: action.text };
    case "SEND_CHAT_MESSAGE": {
      const userMsg: ChatMessage = { id: `msg-${Date.now()}`, role: "user", content: state.quotedText ? `[引用] ${state.quotedText}\n\n${state.chatInput}` : state.chatInput, createdAt: new Date().toISOString() };
      const assistantMsg: ChatMessage = { id: `msg-${Date.now() + 1}`, role: "assistant", content: state.quotedText ? `针对你引用的内容「${state.quotedText.substring(0, 30)}...」回答如下：\n\n这是结合上下文的模拟回复。` : `这是对「${state.chatInput}」的模拟回复。`, createdAt: new Date().toISOString() };
      return { ...state, chatMessages: [...state.chatMessages, userMsg, assistantMsg], chatInput: "", quotedText: null, tokenUsage: state.tokenUsage + 150 };
    }
    case "SET_LOADING": return { ...state, loading: action.loading };
    case "SET_TOKEN_USAGE": return { ...state, tokenUsage: action.usage };
    case "TOGGLE_LEFT_PANEL": return { ...state, leftCollapsed: !state.leftCollapsed };
    case "TOGGLE_RIGHT_PANEL": return { ...state, rightCollapsed: !state.rightCollapsed, rightPanelWidth: state.rightCollapsed ? state.rightPanelWidth || 302 : 0 };
    case "SET_LEFT_WIDTH": return { ...state, leftPanelWidth: Math.max(160, Math.min(302, action.width)) };
    case "SET_RIGHT_WIDTH": {
      const w = Math.min(340, Math.max(189, action.width));
      return { ...state, rightPanelWidth: w, rightCollapsed: false };
    }
    case "SET_DOC_TITLE": return { ...state, documentTitle: action.title };
    default: return state;
  }
}

function WorkspacePage({ workspaceId, initialFiles = [], initialFolders = DEFAULT_FOLDERS, initialSections = [], initialContentBlocks = [], initialFootnotes = [], onOpenSettings }: WorkspacePageProps) {
  const rightDragRef = useRef(false);
  const rightWidthRef = useRef(302);
  const rightDragClientXRef = useRef(0);

  const [leftMode, setLeftMode] = useState<"files" | "sections" | null>("files");
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string>("");
  const [files, setFiles] = useState<FileItem[]>(initialFiles);
  const [documentBlocksByFileId, setDocumentBlocksByFileId] = useState<Record<string, ContentBlock[]>>({});
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [viewerStatus, setViewerStatus] = useState<"idle" | "parsing" | "ready" | "empty" | "error">("idle");

  const [state, dispatch] = useReducer(workspaceReducer, {
    sections: initialSections, selectedSectionId: null, contentBlocks: initialContentBlocks,
    chatMessages: [], chatInput: "", loading: false, footnotes: initialFootnotes,
    expandedFootnoteId: null, currentSelection: null, showSelectionMenu: false,
    selectionMenuPos: null, quotedText: null, tokenUsage: 0,
    leftCollapsed: false, rightCollapsed: false,
    leftPanelWidth: 256, rightPanelWidth: 302, documentTitle: "",
  });

  rightWidthRef.current = state.rightPanelWidth;

  const selectSection = useCallback((sectionId: string) => dispatch({ type: "SELECT_SECTION", sectionId }), []);
  const toggleSectionExpand = useCallback((sectionId: string) => dispatch({ type: "TOGGLE_SECTION_EXPAND", sectionId }), []);
  const updateLineText = useCallback((blockId: string, lineId: string, text: string) => dispatch({ type: "UPDATE_LINE_TEXT", blockId, lineId, text }), []);
  const toggleFootnote = useCallback((footnoteId: string) => dispatch({ type: "TOGGLE_FOOTNOTE", footnoteId }), []);
  const showSelectionMenu = useCallback((show: boolean, pos?: { x: number; y: number }) => dispatch({ type: "SHOW_SELECTION_MENU", show, pos }), []);
  const quoteSelection = useCallback(() => dispatch({ type: "QUOTE_SELECTION" }), []);
  const setChatInput = useCallback((text: string) => dispatch({ type: "SET_CHAT_INPUT", text }), []);
  const clearQuote = useCallback(() => dispatch({ type: "CLEAR_QUOTE" }), []);
  const sendChatMessage = useCallback(() => {
    if ((state.chatInput.trim() || state.quotedText) && !state.loading) {
      dispatch({ type: "SEND_CHAT_MESSAGE" });
    }
  }, [state.chatInput, state.quotedText, state.loading]);
  const setLeftW = useCallback((d: number) => dispatch({ type: "SET_LEFT_WIDTH", width: state.leftPanelWidth + d }), [state.leftPanelWidth]);

  const setRightW = useCallback((d: number, clientX?: number) => {
    rightDragRef.current = true;
    if (clientX !== undefined) {
      rightDragClientXRef.current = clientX;
    }
    if (state.rightCollapsed) {
      rightWidthRef.current = Math.min(667, Math.max(189, 189 - d));
      dispatch({ type: "SET_RIGHT_WIDTH", width: rightWidthRef.current });
    } else {
      const w = Math.max(0, Math.min(667, rightWidthRef.current - d));
      rightWidthRef.current = w;
      dispatch({ type: "SET_RIGHT_WIDTH", width: w });
    }
  }, [state.rightCollapsed]);

  const toggleLeftPanel = useCallback((mode: "files" | "sections") => {
    setLeftMode((prev) => (prev === mode ? null : mode));
    if (state.leftCollapsed) {
      dispatch({ type: "TOGGLE_LEFT_PANEL" });
    }
  }, [state.leftCollapsed]);

  const toggleRightPanel = useCallback(() => {
    dispatch({ type: "TOGGLE_RIGHT_PANEL" });
  }, []);

  // Close on mouseup when at minimum width and cursor near window right edge, or when below threshold
  useEffect(() => {
    const handleMouseUp = () => {
      if (rightDragRef.current) {
        rightDragRef.current = false;
        const winW = window.innerWidth;
        const cx = rightDragClientXRef.current;
        // collapse if below threshold, or at minimum width and cursor within 50px of window right edge
        if (
          (!state.rightCollapsed && state.rightPanelWidth > 0 && state.rightPanelWidth < 189) ||
          (state.rightPanelWidth <= 189 && cx > 0 && winW - cx < 50)
        ) {
          dispatch({ type: "TOGGLE_RIGHT_PANEL" });
        }
      }
    };
    document.addEventListener("mouseup", handleMouseUp);
    return () => document.removeEventListener("mouseup", handleMouseUp);
  }, [state.rightCollapsed, state.rightPanelWidth]);

  // Auto-collapse right panel when viewport is too small to show content properly
  useEffect(() => {
    const handleResize = () => {
      if (state.rightCollapsed) return;
      const toolbarWidth = 40; // left icon bar
      const leftMax = state.leftCollapsed ? 0 : state.leftPanelWidth;
      // Minimum viewport needed: toolbar + left panel width + right panel min (189) + main content min (200)
      const minViewportNeeded = toolbarWidth + leftMax + 189 + 200;
      if (window.innerWidth < minViewportNeeded) {
        dispatch({ type: "TOGGLE_RIGHT_PANEL" });
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [state.rightCollapsed, state.leftCollapsed, state.leftPanelWidth]);

  const applyFileContent = useCallback((fileId: string | null) => {
    if (!fileId) {
      dispatch({ type: "SET_LANG_DATA", sections: [], contentBlocks: [] });
      dispatch({ type: "SELECT_SECTION", sectionId: null });
      setViewerStatus("idle");
      return;
    }

    const selectedFile = files.find((file) => file.id === fileId);
    const hasUploadedContent = !!selectedFile && (
      Object.prototype.hasOwnProperty.call(documentBlocksByFileId, fileId)
      || selectedFile.viewerStatus !== undefined
      || selectedFile.documentId !== undefined
    );

    if (!hasUploadedContent) {
      setViewerStatus("ready");
      return;
    }

    const blocks = documentBlocksByFileId[fileId] ?? [];
    setViewerStatus(selectedFile?.viewerStatus ?? (blocks.length > 0 ? "ready" : "idle"));
    dispatch({ type: "SET_LANG_DATA", sections: [], contentBlocks: blocks });

    if (selectedFile?.viewerStatus === "ready" && blocks.length > 0) {
      dispatch({ type: "SELECT_SECTION", sectionId: UPLOADED_CONTENT_SECTION_ID });
      return;
    }

    dispatch({ type: "SELECT_SECTION", sectionId: null });
  }, [documentBlocksByFileId, files]);

  const handleFileSelect = useCallback((fileId: string, fileName: string) => {
    setSelectedFileId(fileId);
    setSelectedFileName(fileName);
    setLeftMode("sections");
    setUploadError(null);
    applyFileContent(fileId);
  }, [applyFileContent]);

  // 上传文件并调用后端解析流水线。
  // 开发期通过 vite proxy（/api → localhost:8000）访问后端，
  // 生产环境需由部署层或 Tauri 桥接处理路由。
  const handleUpload = useCallback(async (file: File) => {
    const fileId = createFileId();
    const newFile: FileItem = {
      id: fileId,
      name: file.name,
      type: getFileType(file.name),
      category: "",
      size: formatFileSize(file.size),
      date: new Date().toISOString().split("T")[0],
      status: "parsing",
      viewerStatus: "parsing",
    };
    setFiles((prev) => [newFile, ...prev]);
    setSelectedFileId(fileId);
    setSelectedFileName(file.name);
    setLeftMode("sections");
    setUploadError(null);
    setViewerStatus("parsing");
    dispatch({ type: "SET_LANG_DATA", sections: [], contentBlocks: [] });
    dispatch({ type: "SELECT_SECTION", sectionId: null });

    try {
      const uploadResult = await uploadDocument(file, workspaceId ?? "workspace_1");
      const detail = await getDocumentDetail(uploadResult.id);
      const blocks = unitsToContentBlocks(detail.units);
      setDocumentBlocksByFileId((prev) => ({
        ...prev,
        [fileId]: blocks,
      }));
      dispatch({ type: "SET_LANG_DATA", sections: [], contentBlocks: blocks });
      // 自动选中内容区域，让 DocumentViewer 立即渲染解析结果
      if (blocks.length > 0) {
        dispatch({ type: "SELECT_SECTION", sectionId: UPLOADED_CONTENT_SECTION_ID });
        setViewerStatus("ready");
      } else {
        dispatch({ type: "SELECT_SECTION", sectionId: null });
        setViewerStatus("empty");
      }
      setFiles((prev) =>
        prev.map((f) => (f.id === fileId ? {
          ...f,
          status: "parsed",
          documentId: uploadResult.id,
          viewerStatus: blocks.length > 0 ? "ready" : "empty",
        } : f)),
      );
    } catch (err) {
      dispatch({ type: "SET_LANG_DATA", sections: [], contentBlocks: [] });
      dispatch({ type: "SELECT_SECTION", sectionId: null });
      setViewerStatus("error");
      setFiles((prev) =>
        prev.map((f) => (f.id === fileId ? { ...f, status: "pending", viewerStatus: "error" } : f)),
      );
      setUploadError(
        err instanceof Error ? err.message : "未知错误",
      );
    }
  }, [workspaceId]);

  const handleDeleteFile = useCallback((fileId: string) => {
    setFiles((prev) => prev.filter((file) => file.id !== fileId));
    if (selectedFileId === fileId) {
      setSelectedFileId(null);
      setSelectedFileName("");
      setLeftMode("files");
    }
  }, [selectedFileId]);

  const handleRenameFile = useCallback((fileId: string, newName: string) => {
    setFiles((prev) => prev.map((file) => file.id === fileId ? { ...file, name: newName } : file));
    if (selectedFileId === fileId) {
      setSelectedFileName(newName);
    }
  }, [selectedFileId]);

  const handleMoveFile = useCallback((fileId: string, toCategory: string) => {
    setFiles((prev) => prev.map((file) => file.id === fileId ? { ...file, category: toCategory } : file));
  }, []);

  const handleBackToFiles = useCallback(() => {
    setLeftMode("files");
    setSelectedFileId(null);
    applyFileContent(null);
  }, [applyFileContent]);

  const handleSectionSelect = useCallback((id: string) => {
    selectSection(id);
    setTimeout(() => {
      const el = document.getElementById(`block-${id}`);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  }, [selectSection]);

  const showLeftPanel = leftMode !== null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="h-screen bg-[#f5f5f7] text-neutral-800 flex flex-col"
    >
      <div className="flex-1 flex overflow-hidden min-h-0">
        <div className="flex">
          <div className="w-12 flex-shrink-0 bg-white/70 border-r border-black/5 flex flex-col items-center py-3 gap-3">
            <button onClick={() => toggleLeftPanel("files")}
              className={`cursor-pointer w-9 h-9 rounded-lg flex items-center justify-center transition-all ${leftMode === "files" ? "bg-black/10 text-neutral-700" : "text-neutral-400 hover:bg-black/10"}`}
              title="文件管理">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></svg>
            </button>
            {selectedFileId && (
              <button onClick={() => toggleLeftPanel("sections")}
                className={`cursor-pointer w-9 h-9 rounded-lg flex items-center justify-center transition-all ${leftMode === "sections" ? "bg-black/10 text-neutral-700" : "text-neutral-400 hover:bg-black/10"}`}
                title="章节导航">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" /><line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" /></svg>
              </button>
            )}
            <button onClick={toggleRightPanel}
              className={`cursor-pointer w-9 h-9 rounded-lg flex items-center justify-center transition-all ${!state.rightCollapsed ? "bg-black/10 text-neutral-700" : "text-neutral-400 hover:bg-black/10"}`}
              title={state.rightCollapsed ? "展开AI聊天" : "收起AI聊天"}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                <path d="M12 2a7 7 0 0 0-7 7c0 2.4 1.2 4.5 3 5.7V17h8v-2.3c1.8-1.3 3-3.4 3-5.7a7 7 0 0 0-7-7z" />
                <line x1="9" y1="17" x2="15" y2="17" /><line x1="10" y1="20" x2="14" y2="20" />
              </svg>
            </button>
            <div className="flex-1" />
            <button onClick={onOpenSettings} className="cursor-pointer w-9 h-9 rounded-lg flex items-center justify-center text-neutral-400 hover:bg-black/10 transition-all" title="设置">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </button>
          </div>

          <motion.aside
            animate={{ width: !showLeftPanel ? 0 : state.leftPanelWidth, opacity: !showLeftPanel ? 0 : 1 }}
            transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
            className="flex-shrink-0 bg-white/70 border-r border-black/5 backdrop-blur-xl overflow-hidden"
          >
            {showLeftPanel && (
              <div style={{ width: state.leftPanelWidth }} className="h-full relative overflow-hidden">
                <AnimatePresence mode="wait">
                  {leftMode === "files" && (
                    <motion.div key="files-panel" initial={{ x: -state.leftPanelWidth }} animate={{ x: 0 }} exit={{ x: -state.leftPanelWidth }}
                      transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }} className="absolute inset-0 bg-white/70">
                      <FileManager files={files} folders={initialFolders} selectedFileId={selectedFileId}
                        onUpload={handleUpload} onFileSelectWithName={handleFileSelect}
                        onDeleteFile={handleDeleteFile} onRenameFile={handleRenameFile} onMoveFile={handleMoveFile} />
                    </motion.div>
                  )}
                  {leftMode === "sections" && selectedFileId && (
                    <motion.div key="sections-panel" initial={{ x: state.leftPanelWidth }} animate={{ x: 0 }} exit={{ x: state.leftPanelWidth }}
                      transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }} className="absolute inset-0 bg-white/70">
                      <SectionTree sections={state.sections} selectedSectionId={state.selectedSectionId}
                        onSelect={handleSectionSelect} onToggle={toggleSectionExpand} onBack={handleBackToFiles} title={selectedFileName} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}
          </motion.aside>
        </div>

        {showLeftPanel && <ResizableHandle onResize={setLeftW} position="left" />}

        <main className="flex-1 min-w-0 min-h-0">
          {uploadError && (
            <div className="bg-red-50 border-b border-red-200 text-red-700 text-xs px-4 py-2">
              上传失败：{uploadError}
            </div>
          )}
          <DocumentViewer contentBlocks={state.contentBlocks} selectedSectionId={state.selectedSectionId}
            viewerStatus={viewerStatus}
            pendingFileName={selectedFileId ? selectedFileName : undefined}
            errorMessage={uploadError}
            footnotes={state.footnotes} expandedFootnoteId={state.expandedFootnoteId}
            showSelectionMenu={state.showSelectionMenu} selectionMenuPos={state.selectionMenuPos}
            onUpdateLineText={updateLineText}
            onToggleFootnote={toggleFootnote} onShowSelectionMenu={showSelectionMenu} onQuoteSelection={quoteSelection} />
        </main>

        <ResizableHandle onResize={setRightW} position="right" onDoubleClick={toggleRightPanel} />
        <motion.aside
          animate={{ width: state.rightCollapsed ? 0 : state.rightPanelWidth, opacity: state.rightCollapsed ? 0 : 1 }}
          transition={rightDragRef.current ? { duration: 0 } : { duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
          className="flex-shrink-0 bg-white/70 border-l border-black/5 backdrop-blur-xl overflow-hidden"
          style={{ maxWidth: "100vw" }}
        >
          {!state.rightCollapsed && (
            <div style={{ width: state.rightPanelWidth, maxWidth: "100%" }} className="h-full overflow-hidden relative">
              <ChatPanel messages={state.chatMessages} input={state.chatInput} quotedText={state.quotedText} tokenUsage={state.tokenUsage}
                onInputChange={setChatInput} onSend={sendChatMessage} onClearQuote={clearQuote} loading={state.loading} />
            </div>
          )}
        </motion.aside>
      </div>
    </motion.div>
  );
}

export default WorkspacePage;

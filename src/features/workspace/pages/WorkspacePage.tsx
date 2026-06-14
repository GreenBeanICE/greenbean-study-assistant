import { useReducer, useCallback, useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import SectionTree from "../components/left/SectionTree";
import FileManager from "../components/left/FileManager";
import DocumentViewer from "../components/center/DocumentViewer";
import ChatPanel from "../components/right/ChatPanel";
import ResizableHandle from "../components/shared/ResizableHandle";
import type { WorkspaceState, WorkspaceAction, WorkspacePageProps, TextFormatAction } from "../type";
import type { SectionNode, ContentBlock, ContentLine, FootnoteReference } from "../../../types/section";
import type { ChatMessage } from "../../../types/chat";

/** 默认（模拟）章节数据 */
function getLocalizedSections(): SectionNode[] {
  return [
    { id: "ch1", title: "第一章：引言", index: "1", expanded: true, children: [
      { id: "ch1-1", title: "背景介绍", index: "1.1" },
      { id: "ch1-2", title: "研究意义", index: "1.2" },
      { id: "ch1-3", title: "论文结构", index: "1.3" },
    ]},
    { id: "ch2", title: "第二章：理论基础", index: "2", expanded: true, children: [
      { id: "ch2-1", title: "概念定义", index: "2.1" },
      { id: "ch2-2", title: "相关研究", index: "2.2" },
    ]},
    { id: "ch3", title: "第三章：方法论", index: "3", expanded: false, children: [
      { id: "ch3-1", title: "数据采集", index: "3.1" },
      { id: "ch3-2", title: "分析方法", index: "3.2" },
      { id: "ch3-3", title: "验证方案", index: "3.3" },
    ]},
    { id: "ch4", title: "第四章：实验与结果", index: "4" },
    { id: "ch5", title: "第五章：结论", index: "5" },
  ];
}

/** 默认（模拟）内容数据 */
function getLocalizedContent(): ContentBlock[] {
  return [
    { id: "block-ch1-1", sectionId: "ch1-1", title: "1.1 背景介绍", contentType: "text",
      lines: [
        { id: "l1", text: "近年来，人工智能技术取得了飞速发展，深刻改变了各行各业的面貌。", type: "paragraph", footnoteRef: "1" },
        { id: "l2", text: "在教育领域，AI 技术的应用尤为引人注目。", type: "paragraph" },
        { id: "l3", text: "本节将介绍本研究的基本背景和动机。", type: "heading", level: 2 },
        { id: "l4", text: "• 全球教育数字化转型趋势", type: "list" },
        { id: "l5", text: "• 在法中国留学生面临的语言与学习障碍", type: "list" },
        { id: "l6", text: "• 现有工具与解决方案的不足", type: "list", footnoteRef: "2" },
      ]},
    { id: "block-table-1", sectionId: "ch2-1", title: "表1：主流AI教育平台对比", contentType: "table",
      tableData: { headers: ["平台名称", "语言支持", "AI 功能", "定价"],
        rows: [
          { id: "tr1", cells: ["Coursera", "多语言", "课程推荐", "$59/月"] },
          { id: "tr2", cells: ["Duolingo", "40+语言", "自适应学习", "免费+Premium"] },
          { id: "tr3", cells: ["GreenBean", "中/法", "深度解析+问答", "免费"] },
        ]},
    },
    { id: "block-image-1", sectionId: "ch2-1", title: "图1：AI教育市场规模预测", contentType: "image", imageUrl: "",
      imageCaption: "全球AI教育市场将在2025年突破500亿美元（示意图）" },
    { id: "block-ch1-2", sectionId: "ch1-2", title: "1.2 研究意义", contentType: "text",
      lines: [
        { id: "l7", text: "本研究具有重要的理论意义和实践价值。", type: "paragraph" },
        { id: "l8", text: "从理论层面看，本研究探索了 AI 辅助学习的新范式。", type: "paragraph" },
        { id: "l9", text: "从实践层面看，本研究为留学生提供了切实可行的学习工具。", type: "paragraph" },
      ]},
    { id: "block-ch2-1", sectionId: "ch2-1", title: "2.1 概念定义", contentType: "text",
      lines: [
        { id: "l10", text: "本节定义了研究中使用的核心概念。", type: "paragraph" },
        { id: "l11", text: "定义 1（智能学习助手）：...", type: "code" },
        { id: "l12", text: "定义 2（知识图谱）：...", type: "code" },
      ]},
  ];
}

const initialFootnotes: FootnoteReference[] = [
  { id: "fn-1", refNumber: "1", sourceText: "Gartner预测到2025年AI在教育领域创造超过500亿美元的市场价值。", sourceDesc: "第1页，第1段" },
  { id: "fn-2", refNumber: "2", sourceText: "现有针对在法中国留学生的法语AI辅导产品仍属空白。", sourceDesc: "第1页，第6段" },
];

function workspaceReducer(state: WorkspaceState, action: WorkspaceAction): WorkspaceState {
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
    case "TOGGLE_RIGHT_PANEL": return { ...state, rightCollapsed: !state.rightCollapsed };
    case "SET_LEFT_WIDTH": return { ...state, leftPanelWidth: Math.max(160, Math.min(400, action.width)) };
    case "SET_RIGHT_WIDTH": return { ...state, rightPanelWidth: Math.max(200, Math.min(500, action.width)) };
    case "SET_DOC_TITLE": return { ...state, documentTitle: action.title };
    default: return state;
  }
}

function WorkspacePage(_props: WorkspacePageProps) {
  const titleRef = useRef<HTMLInputElement>(null);

  // 左侧面板模式: "files"（文件列表）| "sections"（章节树）
  const [leftMode, setLeftMode] = useState<"files" | "sections">("files");
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string>("");
  const [rightDragging, setRightDragging] = useState(false);

  const [state, dispatch] = useReducer(workspaceReducer, {
    sections: getLocalizedSections(), selectedSectionId: null, contentBlocks: getLocalizedContent(),
    chatMessages: [], chatInput: "", loading: false, footnotes: initialFootnotes,
    expandedFootnoteId: null, currentSelection: null, showSelectionMenu: false,
    selectionMenuPos: null, quotedText: null, tokenUsage: 0,
    leftCollapsed: false, rightCollapsed: false,
    leftPanelWidth: 256, rightPanelWidth: 300, documentTitle: "cours-analyse-s1.pdf",
  });

  const d = useCallback((s: string) => dispatch({ type: "SELECT_SECTION", sectionId: s } as any), []);
  const togg = useCallback((s: string) => dispatch({ type: "TOGGLE_SECTION_EXPAND", sectionId: s } as any), []);
  const th = useCallback((b: string, l: string) => dispatch({ type: "TOGGLE_HIGHLIGHT", blockId: b, lineId: l } as any), []);
  const ut = useCallback((b: string, l: string, t: string) => dispatch({ type: "UPDATE_LINE_TEXT", blockId: b, lineId: l, text: t } as any), []);
  const fmt = useCallback((b: string, l: string, f: TextFormatAction) => dispatch({ type: "FORMAT_LINE", blockId: b, lineId: l, format: f } as any), []);
  const tf = useCallback((id: string) => dispatch({ type: "TOGGLE_FOOTNOTE", footnoteId: id } as any), []);
  const sel = useCallback((s: any) => dispatch({ type: "SET_SELECTION", selection: s } as any), []);
  const sm = useCallback((s: boolean, p?: { x: number; y: number }) => dispatch({ type: "SHOW_SELECTION_MENU", show: s, pos: p } as any), []);
  const qs = useCallback(() => dispatch({ type: "QUOTE_SELECTION" } as any), []);
  const ci = useCallback((t: string) => dispatch({ type: "SET_CHAT_INPUT", text: t } as any), []);
  const cq = useCallback(() => dispatch({ type: "CLEAR_QUOTE" } as any), []);
  const send = useCallback(() => { if ((state.chatInput.trim() || state.quotedText) && !state.loading) dispatch({ type: "SEND_CHAT_MESSAGE", message: {} as ChatMessage } as any); }, [state.chatInput, state.quotedText, state.loading]);
  const tl = useCallback(() => dispatch({ type: "TOGGLE_LEFT_PANEL" } as any), []);
  const tr = useCallback(() => dispatch({ type: "TOGGLE_RIGHT_PANEL" } as any), []);
  const setLeftW = useCallback((d: number) => dispatch({ type: "SET_LEFT_WIDTH", width: state.leftPanelWidth + d } as any), [state.leftPanelWidth]);
  const setRightW = useCallback((d: number) => dispatch({ type: "SET_RIGHT_WIDTH", width: state.rightPanelWidth - d } as any), [state.rightPanelWidth]);

  /** 文件选择：文件栏向左滑出，章节栏从右侧滑入 */
  const handleFileSelect = useCallback((fileId: string, fileName: string) => {
    setSelectedFileId(fileId);
    setSelectedFileName(fileName);
    setLeftMode("sections");
  }, []);

  /** 返回文件列表：章节栏向右滑出，文件栏从左侧滑入 */
  const handleBackToFiles = useCallback(() => {
    setLeftMode("files");
    setSelectedFileId(null);
  }, []);

  const handleSectionSelect = useCallback((id: string) => {
    d(id);
    setTimeout(() => {
      const el = document.getElementById(`block-${id}`);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  }, [d]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="h-screen bg-[#f5f5f7] text-neutral-800 flex flex-col"
    >
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* 左侧面板区 */}
        <div className="flex">
          {/* 左工具栏 */}
          <div className="w-10 flex-shrink-0 bg-white/70 border-r border-black/5 flex flex-col items-center py-2 gap-2">
            <button onClick={tl} className="cursor-pointer w-7 h-7 rounded-md flex items-center justify-center hover:bg-black/10 text-neutral-400" title="收起章节">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="6" height="18" rx="1" /><line x1="11" y1="3" x2="21" y2="3" /><line x1="11" y1="9" x2="21" y2="9" /><line x1="11" y1="15" x2="21" y2="15" /></svg>
            </button>
            <div className="w-6 border-t border-black/10" />
            <button
              onClick={() => setLeftMode("files")}
              className={`cursor-pointer w-7 h-7 rounded-md flex items-center justify-center transition-all ${
                leftMode === "files" ? "bg-black/10 text-neutral-700" : "text-neutral-400 hover:bg-black/10"
              }`}
              title="文件管理"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></svg>
            </button>
            {selectedFileId && (
              <button
                onClick={() => setLeftMode("sections")}
                className={`cursor-pointer w-7 h-7 rounded-md flex items-center justify-center transition-all ${
                  leftMode === "sections" ? "bg-black/10 text-neutral-700" : "text-neutral-400 hover:bg-black/10"
                }`}
                title="章节导航"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" /><line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" /></svg>
              </button>
            )}
            <div className="w-6 border-t border-black/10 my-1" />
            <button onClick={tr}
              className={`cursor-pointer w-7 h-7 rounded-md flex items-center justify-center transition-all ${
                !state.rightCollapsed ? "bg-black/10 text-neutral-700" : "text-neutral-400 hover:bg-black/10"
              }`}
              title={state.rightCollapsed ? "展开聊天" : "收起聊天"}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                <path d="M12 2a7 7 0 0 0-7 7c0 2.4 1.2 4.5 3 5.7V17h8v-2.3c1.8-1.3 3-3.4 3-5.7a7 7 0 0 0-7-7z" />
                <line x1="9" y1="17" x2="15" y2="17" />
                <line x1="10" y1="20" x2="14" y2="20" />
              </svg>
            </button>
            <div className="flex-1" />
          </div>

          {/* 左侧面板 */}
          <motion.aside
            animate={{
              width: state.leftCollapsed ? 0 : state.leftPanelWidth,
              opacity: state.leftCollapsed ? 0 : 1,
            }}
            transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
            className="flex-shrink-0 bg-white/70 border-r border-black/5 backdrop-blur-xl overflow-hidden"
          >
            {!state.leftCollapsed && (
              <div style={{ width: state.leftPanelWidth }} className="h-full relative overflow-hidden">
                <AnimatePresence mode="wait">
                  {leftMode === "files" && (
                    <motion.div
                      key="files-panel"
                      initial={{ x: -state.leftPanelWidth }}
                      animate={{ x: 0 }}
                      exit={{ x: -state.leftPanelWidth }}
                      transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
                      className="absolute inset-0 bg-white/70"
                    >
                      <FileManager onFileSelectWithName={handleFileSelect} />
                    </motion.div>
                  )}
                  {leftMode === "sections" && selectedFileId && (
                    <motion.div
                      key="sections-panel"
                      initial={{ x: state.leftPanelWidth }}
                      animate={{ x: 0 }}
                      exit={{ x: state.leftPanelWidth }}
                      transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
                      className="absolute inset-0 bg-white/70"
                    >
                      <SectionTree
                        sections={state.sections}
                        selectedSectionId={state.selectedSectionId}
                        onSelect={handleSectionSelect}
                        onToggle={togg}
                        onBack={handleBackToFiles}
                        title={selectedFileName}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}
          </motion.aside>
        </div>

        {!state.leftCollapsed && <ResizableHandle onResize={setLeftW} position="left" />}

        {/* 中间文档区域 */}
        <main className="flex-1 min-w-0 min-h-0">
          <DocumentViewer
            contentBlocks={state.contentBlocks} selectedSectionId={state.selectedSectionId}
            footnotes={state.footnotes} expandedFootnoteId={state.expandedFootnoteId}
            currentSelection={state.currentSelection} showSelectionMenu={state.showSelectionMenu} selectionMenuPos={state.selectionMenuPos}
            onToggleHighlight={th} onUpdateLineText={ut} onFormatLine={fmt}
            onToggleFootnote={tf} onSelectText={sel} onShowSelectionMenu={sm} onQuoteSelection={qs} />
        </main>

        {/* 右侧聊天面板 */}
        <ResizableHandle onResize={setRightW} position="right" onDoubleClick={tr} onDragStateChange={setRightDragging} />
        <aside
          className={`flex-shrink-0 bg-white/70 border-l border-black/5 backdrop-blur-xl overflow-hidden ${
            rightDragging ? "" : "transition-all duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1)]"
          }`}
          style={{
            width: state.rightCollapsed ? 28 : state.rightPanelWidth,
            minWidth: state.rightCollapsed ? 28 : 220,
            maxWidth: state.rightCollapsed ? 28 : "33.33vw",
          }}
        >
          {state.rightCollapsed ? (
            <button
              onClick={tr}
              title="展开聊天"
              className="w-7 h-full flex flex-col items-center justify-center cursor-pointer hover:bg-black/10 transition-all duration-200 group"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="text-neutral-400 group-hover:text-neutral-700 transition-colors mb-1">
                <path d="M12 2a7 7 0 0 0-7 7c0 2.4 1.2 4.5 3 5.7V17h8v-2.3c1.8-1.3 3-3.4 3-5.7a7 7 0 0 0-7-7z" />
                <line x1="9" y1="17" x2="15" y2="17" />
                <line x1="10" y1="20" x2="14" y2="20" />
              </svg>
              <span className="text-[8px] text-neutral-400 group-hover:text-neutral-600 transition-colors tracking-wider font-medium [writing-mode:vertical-rl]">
                展开聊天
              </span>
            </button>
          ) : (
            <div className="h-full w-full overflow-hidden">
              <ChatPanel messages={state.chatMessages} input={state.chatInput} quotedText={state.quotedText} tokenUsage={state.tokenUsage}
                onInputChange={ci} onSend={send} onClearQuote={cq} loading={state.loading} />
            </div>
          )}
        </aside>
      </div>
    </motion.div>
  );
}

export default WorkspacePage;
import { useReducer, useCallback, useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { useI18n } from "../../../lib/i18n";
import SectionTree from "../components/left/SectionTree";
import FileManager from "../components/left/FileManager";
import DocumentViewer from "../components/center/DocumentViewer";
import ChatPanel from "../components/right/ChatPanel";
import ResizableHandle from "../components/shared/ResizableHandle";
import type { WorkspaceState, WorkspaceAction, WorkspacePageProps, TextFormatAction } from "../type";
import type { SectionNode, ContentBlock, ContentLine, FootnoteReference } from "../../../types/section";
import type { ChatMessage } from "../../../types/chat";

function getLocalizedSections(lang: string): SectionNode[] {
  const zh = lang === "zh"; 
  return [
    { id: "ch1", title: zh ? "第一章：引言" : "Ch.1 Introduction", index: "1", expanded: true, children: [
      { id: "ch1-1", title: zh ? "背景介绍" : "Contexte", index: "1.1" },
      { id: "ch1-2", title: zh ? "研究意义" : "Importance", index: "1.2" },
      { id: "ch1-3", title: zh ? "论文结构" : "Structure", index: "1.3" },
    ]},
    { id: "ch2", title: zh ? "第二章：理论基础" : "Ch.2 Fondements", index: "2", expanded: true, children: [
      { id: "ch2-1", title: zh ? "概念定义" : "Définitions", index: "2.1" },
      { id: "ch2-2", title: zh ? "相关研究" : "Travaux connexes", index: "2.2" },
    ]},
    { id: "ch3", title: zh ? "第三章：方法论" : "Ch.3 Méthodologie", index: "3", expanded: false, children: [
      { id: "ch3-1", title: zh ? "数据采集" : "Collecte", index: "3.1" },
      { id: "ch3-2", title: zh ? "分析方法" : "Analyse", index: "3.2" },
      { id: "ch3-3", title: zh ? "验证方案" : "Validation", index: "3.3" },
    ]},
    { id: "ch4", title: zh ? "第四章：实验与结果" : "Ch.4 Expériences", index: "4" },
    { id: "ch5", title: zh ? "第五章：结论" : "Ch.5 Conclusion", index: "5" },
  ];
}

function getLocalizedContent(lang: string): ContentBlock[] {
  const zh = lang === "zh"; const fr = lang === "fr";
  return [
    { id: "block-ch1-1", sectionId: "ch1-1", title: zh ? "1.1 背景介绍" : "1.1 Contexte", contentType: "text",
      lines: [
        { id: "l1", text: zh ? "近年来，人工智能技术取得了飞速发展，深刻改变了各行各业的面貌。" : "L'IA a connu un développement rapide, transformant les industries.", type: "paragraph", footnoteRef: "1" },
        { id: "l2", text: zh ? "在教育领域，AI 技术的应用尤为引人注目。" : "Dans l'éducation, l'IA permet un apprentissage personnalisé.", type: "paragraph" },
        { id: "l3", text: zh ? "本节将介绍本研究的基本背景和动机。" : "Cette section présente le contexte et la motivation.", type: "heading", level: 2 },
        { id: "l4", text: zh ? "• 全球教育数字化转型趋势" : "• Transformation numérique de l'éducation", type: "list" },
        { id: "l5", text: zh ? "• 在法中国留学生面临的语言与学习障碍" : "• Barrières linguistiques des étudiants chinois en France", type: "list" },
        { id: "l6", text: zh ? "• 现有工具与解决方案的不足" : "• Limites des outils existants", type: "list", footnoteRef: "2" },
      ]},
    { id: "block-table-1", sectionId: "ch2-1", title: zh ? "表1：主流AI教育平台对比" : "Tableau 1: Plateformes IA", contentType: "table",
      tableData: { headers: zh ? ["平台名称", "语言支持", "AI 功能", "定价"] : ["Plateforme", "Langues", "IA", "Prix"],
        rows: [
          { id: "tr1", cells: zh ? ["Coursera", "多语言", "课程推荐", "$59/月"] : ["Coursera", "Multi", "Recommandation", "59$/mois"] },
          { id: "tr2", cells: zh ? ["Duolingo", "40+语言", "自适应学习", "免费+Premium"] : ["Duolingo", "40+", "Adaptatif", "Gratuit+Premium"] },
          { id: "tr3", cells: zh ? ["GreenBean", "中/法", "深度解析+问答", "免费"] : ["GreenBean", "ZH/FR", "Analyse+QA", "Gratuit"] },
        ]},
    },
    { id: "block-image-1", sectionId: "ch2-1", title: zh ? "图1：AI教育市场规模预测" : "Fig.1: Marché de l'IA éducative", contentType: "image", imageUrl: "",
      imageCaption: zh ? "全球AI教育市场将在2025年突破500亿美元（示意图）" : "Marché mondial de l'IA éducative dépassera 50Md$ d'ici 2025" },
    { id: "block-ch1-2", sectionId: "ch1-2", title: zh ? "1.2 研究意义" : "1.2 Importance", contentType: "text",
      lines: [
        { id: "l7", text: zh ? "本研究具有重要的理论意义和实践价值。" : "Cette recherche a une valeur théorique et pratique.", type: "paragraph" },
        { id: "l8", text: zh ? "从理论层面看，本研究探索了 AI 辅助学习的新范式。" : "Théoriquement, elle explore de nouveaux paradigmes d'apprentissage.", type: "paragraph" },
        { id: "l9", text: zh ? "从实践层面看，本研究为留学生提供了切实可行的学习工具。" : "Pratiquement, elle offre un outil d'étude pour les étudiants.", type: "paragraph" },
      ]},
    { id: "block-ch2-1", sectionId: "ch2-1", title: zh ? "2.1 概念定义" : "2.1 Définitions", contentType: "text",
      lines: [
        { id: "l10", text: zh ? "本节定义了研究中使用的核心概念。" : "Cette section définit les concepts clés.", type: "paragraph" },
        { id: "l11", text: zh ? "定义 1（智能学习助手）：..." : "Déf.1 (Assistant IA) : ...", type: "code" },
        { id: "l12", text: zh ? "定义 2（知识图谱）：..." : "Déf.2 (Graphe de connaissances) : ...", type: "code" },
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

function WorkspacePage({ onBack, dark, setDark, lang, setLang, onLogout }: WorkspacePageProps) {
  const { t } = useI18n();
  const titleRef = useRef<HTMLInputElement>(null);

  // 左侧面板切换: "sections" | "files" | "both"
  const [leftPanelMode, setLeftPanelMode] = useState<"sections" | "files">("sections");
  
  const [state, dispatch] = useReducer(workspaceReducer, {
    sections: getLocalizedSections(lang), selectedSectionId: null, contentBlocks: getLocalizedContent(lang),
    chatMessages: [], chatInput: "", loading: false, footnotes: initialFootnotes,
    expandedFootnoteId: null, currentSelection: null, showSelectionMenu: false,
    selectionMenuPos: null, quotedText: null, tokenUsage: 0,
    leftCollapsed: false, rightCollapsed: false,
    leftPanelWidth: 256, rightPanelWidth: 320, documentTitle: "cours-analyse-s1.pdf",
  });

  useEffect(() => {
    dispatch({ type: "SET_LANG_DATA", sections: getLocalizedSections(lang), contentBlocks: getLocalizedContent(lang) } as any);
  }, [lang]);

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
      className="min-h-screen bg-[#f5f5f7] dark:bg-[#0a0a0a] text-neutral-800 dark:text-neutral-200 transition-colors duration-300 flex flex-col"
    >
      <header className="flex-shrink-0 h-14 backdrop-blur-xl bg-white/80 dark:bg-black/70 border-b border-black/5 dark:border-white/10 flex items-center px-2 md:px-4 gap-1 md:gap-3 z-10">
        <button onClick={onBack} className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/10 transition" title={t("navFeatures")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="15 18 9 12 15 6" /></svg>
        </button>
        <a href="#" onClick={(e) => { e.preventDefault(); onBack?.(); }} className="text-base font-semibold tracking-tight select-none">GreenBean</a>
        <span className="hidden md:inline text-[11px] text-neutral-400 dark:text-neutral-500 bg-black/5 dark:bg-white/10 px-2 py-0.5 rounded-full">{t("wsTitle")}</span>
        <div className="flex items-center gap-1 ml-auto">
          <button onClick={() => setLang(lang === "zh" ? "fr" : "zh")} className="px-2 py-1 rounded-full text-[11px] font-medium text-neutral-600 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/10 transition">{lang === "zh" ? "FR" : "中文"}</button>
          <button onClick={onLogout} className="px-2.5 py-1 rounded-full text-[11px] font-medium text-neutral-600 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/10 transition" title={t("logout")}>{t("logout")}</button>
          <button onClick={() => setDark((p) => !p)} className="w-7 h-7 rounded-full flex items-center justify-center text-sm hover:bg-black/5 dark:hover:bg-white/10 transition">
            {dark ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /></svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>
            )}
          </button>
        </div>
      </header>

      {state.selectedSectionId && (
        <div className="flex-shrink-0 px-4 py-1.5 bg-white/40 dark:bg-white/[0.02] border-b border-black/5 dark:border-white/10 flex items-center gap-2">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-neutral-400"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
          <input ref={titleRef} value={state.documentTitle} onChange={(e) => dispatch({ type: "SET_DOC_TITLE", title: e.target.value } as any)}
            className="flex-1 bg-transparent text-xs text-neutral-500 dark:text-neutral-400 outline-none border-none focus:text-neutral-700 dark:focus:text-neutral-200 transition" />
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        {/* 左侧面板 */}
        <div className="flex">
          <div className="w-10 flex-shrink-0 bg-white/70 dark:bg-white/[0.03] border-r border-black/5 dark:border-white/10 flex flex-col items-center py-2 gap-2">
            <button onClick={tl} className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-black/10 dark:hover:bg-white/10 text-neutral-400 dark:text-neutral-500" title={t("wsCollapseSection")}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="6" height="18" rx="1" /><line x1="11" y1="3" x2="21" y2="3" /><line x1="11" y1="9" x2="21" y2="9" /><line x1="11" y1="15" x2="21" y2="15" /></svg>
            </button>
            <div className="w-6 border-t border-black/10 dark:border-white/10" />
            <button
              onClick={() => setLeftPanelMode("sections")}
              className={`w-7 h-7 rounded-md flex items-center justify-center transition-all ${
                leftPanelMode === "sections"
                  ? "bg-black/10 dark:bg-white/10 text-neutral-700 dark:text-neutral-200"
                  : "text-neutral-400 dark:text-neutral-500 hover:bg-black/5 dark:hover:bg-white/10"
              }`}
              title={t("wsSectionNav")}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" /><line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" /></svg>
            </button>
            <button
              onClick={() => setLeftPanelMode("files")}
              className={`w-7 h-7 rounded-md flex items-center justify-center transition-all ${
                leftPanelMode === "files"
                  ? "bg-black/10 dark:bg-white/10 text-neutral-700 dark:text-neutral-200"
                  : "text-neutral-400 dark:text-neutral-500 hover:bg-black/5 dark:hover:bg-white/10"
              }`}
              title={t("wsFileTitle")}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></svg>
            </button>
          </div>
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={state.leftCollapsed ? { width: 0, opacity: 0 } : { width: state.leftPanelWidth, opacity: 1 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="flex-shrink-0 bg-white/70 dark:bg-white/[0.03] border-r border-black/5 dark:border-white/10 backdrop-blur-xl overflow-hidden"
          >
            {!state.leftCollapsed && (
              <div style={{ width: state.leftPanelWidth }}>
                {leftPanelMode === "sections" ? (
                  <SectionTree sections={state.sections} selectedSectionId={state.selectedSectionId} onSelect={handleSectionSelect} onToggle={togg} />
                ) : (
                  <FileManager />
                )}
              </div>
            )}
          </motion.aside>
        </div>
        {!state.leftCollapsed && <ResizableHandle onResize={setLeftW} position="left" />}

        <main className="flex-1 min-w-0">
          <DocumentViewer
            contentBlocks={state.contentBlocks} selectedSectionId={state.selectedSectionId}
            footnotes={state.footnotes} expandedFootnoteId={state.expandedFootnoteId}
            currentSelection={state.currentSelection} showSelectionMenu={state.showSelectionMenu} selectionMenuPos={state.selectionMenuPos}
            onToggleHighlight={th} onUpdateLineText={ut} onFormatLine={fmt}
            onToggleFootnote={tf} onSelectText={sel} onShowSelectionMenu={sm} onQuoteSelection={qs} />
        </main>

        {!state.rightCollapsed && <ResizableHandle onResize={setRightW} position="right" />}
        <div className="flex flex-row-reverse">
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={state.rightCollapsed ? { width: 0, opacity: 0 } : { width: state.rightPanelWidth, opacity: 1 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="flex-shrink-0 bg-white/70 dark:bg-white/[0.03] border-l border-black/5 dark:border-white/10 backdrop-blur-xl overflow-hidden"
          >
            {!state.rightCollapsed && (
              <div className="h-full" style={{ width: state.rightPanelWidth }}>
                <ChatPanel messages={state.chatMessages} input={state.chatInput} quotedText={state.quotedText} tokenUsage={state.tokenUsage}
                  onInputChange={ci} onSend={send} onClearQuote={cq} loading={state.loading} />
              </div>
            )}
          </motion.aside>
          <div className="w-10 flex-shrink-0 bg-white/70 dark:bg-white/[0.03] border-l border-black/5 dark:border-white/10 flex flex-col items-center py-2 gap-2">
            <button onClick={tr} className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-black/10 dark:hover:bg-white/10 text-neutral-400 dark:text-neutral-500" title={state.rightCollapsed ? t("wsExpandChat") : t("wsCollapseChat")}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default WorkspacePage;
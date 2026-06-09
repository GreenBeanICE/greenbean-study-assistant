import { useRef, useCallback, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useI18n } from "../../../../lib/i18n";
import DocumentToolbar from "../shared/DocumentToolbar";
import type { DocumentViewerProps } from "../../type";
import type { ContentLine, ContentBlock, FootnoteReference } from "../../../../types/section";
import type { TextFormatAction } from "../../type";

/** 只控制行级对齐和整体外观，加粗/斜体等通过内联 HTML 实现 */
function getLineStyle(line: ContentLine): string {
  const c: string[] = [];
  switch (line.type) {
    case "heading":
      c.push("font-semibold");
      if (line.level === 1) c.push("text-xl mt-6 mb-3");
      else if (line.level === 2) c.push("text-lg mt-4 mb-2");
      else c.push("text-base mt-3 mb-1");
      break;
    case "list": c.push("pl-4 text-sm"); break;
    case "code": c.push("font-mono text-sm"); break;
    default: c.push("text-sm leading-relaxed");
  }
  if (line.underline) c.push("underline underline-offset-2");
  if (line.align === "center") c.push("text-center");
  else if (line.align === "right") c.push("text-right");
  else if (line.align === "justify") c.push("text-justify");
  return c.join(" ");
}

/** 可交互的内容行：支持选中部分文字 + 内联编辑 */
function ContentLineRender({ line, blockId, onViewFootnote, onLineHtmlChange }: {
  line: ContentLine;
  blockId: string;
  onViewFootnote?: (ref: string) => void;
  onLineHtmlChange?: (blockId: string, lineId: string, html: string) => void;
}) {
  const { t } = useI18n();
  const spanRef = useRef<HTMLSpanElement>(null);

  const handleFootnoteClick = useCallback((e: React.MouseEvent, ref: string) => {
    e.stopPropagation();
    e.preventDefault();
    if (onViewFootnote) onViewFootnote(ref);
  }, [onViewFootnote]);

  // contentEditable 失去焦点时保存 HTML
  const handleBlur = useCallback(() => {
    if (spanRef.current && onLineHtmlChange) {
      const html = spanRef.current.innerHTML;
      if (html !== line.text) {
        onLineHtmlChange(blockId, line.id, html);
      }
    }
  }, [blockId, line.id, line.text, onLineHtmlChange]);

  // 检测是否有内联 HTML 标签
  const hasInlineHtml = /<[a-zA-Z]/.test(line.text);

  return (
    <div
      data-block-id={blockId}
      data-line-id={line.id}
      className={`px-1 py-0.5 rounded-sm transition-colors ${
        line.highlighted
          ? "bg-yellow-200/60 dark:bg-yellow-400/20"
          : "hover:bg-black/[0.02] dark:hover:bg-white/[0.02]"
      } ${line.type === "code" ? "font-mono text-sm bg-black/5 dark:bg-white/10 rounded px-2 py-1" : ""}`}
    >
      <span
        ref={spanRef}
        contentEditable={true}
        suppressContentEditableWarning={true}
        onBlur={handleBlur}
        className={`outline-none cursor-text ${getLineStyle(line)}`}
        style={{ color: line.color || undefined, backgroundColor: line.highlighted ? "rgba(254,240,138,0.4)" : undefined }}
        dangerouslySetInnerHTML={hasInlineHtml ? { __html: line.text } : undefined}
      >
        {hasInlineHtml ? null : line.text}
      </span>
      {line.footnoteRef && (
        <button
          onClick={(e) => handleFootnoteClick(e, line.footnoteRef!)}
          className="inline-flex items-center justify-center w-4 h-4 ml-1 text-[10px] font-medium text-blue-600 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/40 rounded-full cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-800/50 transition-colors align-super flex-shrink-0"
          title={t("wsViewFootnote")}
        >
          {line.footnoteRef}
        </button>
      )}
    </div>
  );
}

function TableBlock({ block }: { block: ContentBlock }) {
  if (!block.tableData) return null;
  const { headers, rows } = block.tableData;
  return (
    <div className="overflow-x-auto my-3">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-black/5 dark:bg-white/10">
            {headers.map((h, i) => (
              <th key={i} className="px-4 py-2 text-left font-semibold text-neutral-700 dark:text-neutral-300 border-b border-black/10 dark:border-white/10 text-xs">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-black/5 dark:border-white/5">
              {row.cells.map((cell, i) => (
                <td key={i} className="px-4 py-2 text-neutral-600 dark:text-neutral-400 text-xs">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ImageBlock({ block }: { block: ContentBlock }) {
  return (
    <div className="flex flex-col items-center my-4">
      <div className={`w-full max-w-md aspect-video rounded-lg ${block.imageUrl ? "" : "bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-500/10 dark:to-purple-500/10"} flex items-center justify-center border border-black/5 dark:border-white/10`}>
        {block.imageUrl ? (
          <img src={block.imageUrl} alt={block.imageCaption || block.title} className="w-full h-full object-contain rounded-lg" />
        ) : (
          <div className="text-center p-6">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="text-blue-400 dark:text-blue-500/50 mx-auto mb-2">
              <rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" />
            </svg>
            <p className="text-xs text-neutral-400 dark:text-neutral-500">Chart</p>
          </div>
        )}
      </div>
      {block.imageCaption && (
        <p className="mt-1.5 text-xs text-neutral-500 dark:text-neutral-400 text-center italic">{block.imageCaption}</p>
      )}
    </div>
  );
}

function SelectionMenu({ pos, onQuote, onClose }: { pos: { x: number; y: number }; onQuote: () => void; onClose: () => void }) {
  const { t } = useI18n();
  return (<><div className="fixed inset-0 z-40" onClick={onClose} />
    <div className="fixed z-50 bg-white dark:bg-neutral-800 rounded-xl shadow-xl border border-black/10 dark:border-white/10 py-1 min-w-[140px]" style={{ left: pos.x, top: pos.y }}>
      <button onClick={onQuote} className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-neutral-700 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/10 transition">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
        {t("wsQuoteAction")}
      </button>
    </div>
  </>);
}

function FootnotePanel({ footnote, onClose }: { footnote: FootnoteReference; onClose: () => void }) {
  return (
    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="border-t border-black/5 dark:border-white/10 overflow-hidden">
      <div className="px-4 py-3 bg-blue-50/50 dark:bg-blue-500/5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center justify-center w-5 h-5 text-[10px] font-bold text-blue-600 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/40 rounded-full">{footnote.refNumber}</span>
              <span className="text-[11px] text-neutral-400 dark:text-neutral-500 font-medium">{footnote.sourceDesc}</span>
            </div>
            <p className="text-sm text-neutral-600 dark:text-neutral-300 leading-relaxed">{footnote.sourceText}</p>
          </div>
          <button onClick={onClose} className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center hover:bg-black/10 dark:hover:bg-white/10 transition">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function BlockContent({ block, onViewFootnote, onLineHtmlChange }: {
  block: ContentBlock;
  onViewFootnote?: (ref: string) => void;
  onLineHtmlChange?: (blockId: string, lineId: string, html: string) => void;
}) {
  if (block.contentType === "table") return <TableBlock block={block} />;
  if (block.contentType === "image") return <ImageBlock block={block} />;
  return (
    <div className="space-y-0.5">
      {(block.lines || []).map((line) => (
        <ContentLineRender key={line.id} line={line} blockId={block.id} onViewFootnote={onViewFootnote} onLineHtmlChange={onLineHtmlChange} />
      ))}
    </div>
  );
}

function DocumentViewer({
  contentBlocks, selectedSectionId, footnotes, expandedFootnoteId,
  currentSelection, showSelectionMenu, selectionMenuPos,
  onToggleHighlight, onUpdateLineText, onFormatLine, onToggleFootnote,
  onSelectText, onShowSelectionMenu, onQuoteSelection,
}: DocumentViewerProps) {
  const { t } = useI18n();
  const viewerRef = useRef<HTMLDivElement>(null);
  const lastRangeRef = useRef<Range | null>(null);

  const filteredBlocks = selectedSectionId
    ? contentBlocks.filter((block) => block.sectionId === selectedSectionId)
    : [];
  const showEmptyState = !selectedSectionId;

  // 选中文本后弹出菜单（引用询问AI）— 菜单位于选中文字右侧，不遮挡文字
  useEffect(() => {
    const handleMouseUp = () => {
      const s = window.getSelection();
      if (s && s.toString().trim().length > 0 && selectedSectionId) {
        try {
          const range = s.getRangeAt(0);
          lastRangeRef.current = range.cloneRange();
          const rect = range.getBoundingClientRect();
          onSelectText({ text: s.toString().trim(), blockId: "", sectionId: selectedSectionId, fromLineId: "", toLineId: "" });
          onShowSelectionMenu(true, { x: rect.right + 8, y: rect.top });
        } catch { /* noop */ }
        return;
      }
      setTimeout(() => { if (!window.getSelection()?.toString().trim()) { onSelectText(null); onShowSelectionMenu(false); } }, 100);
    };
    document.addEventListener("mouseup", handleMouseUp);
    return () => document.removeEventListener("mouseup", handleMouseUp);
  }, [selectedSectionId, onSelectText, onShowSelectionMenu]);

  // 监听选中变化，同步 hasSelection 状态用于工具栏按钮启用
  const [hasSelection, setHasSelection] = useState(false);
  useEffect(() => {
    const handleSelectionChange = () => {
      const s = window.getSelection();
      setHasSelection(!!(s && s.toString().trim().length > 0 && selectedSectionId));
    };
    document.addEventListener("selectionchange", handleSelectionChange);
    return () => document.removeEventListener("selectionchange", handleSelectionChange);
  }, [selectedSectionId]);

  // contentEditable 内容变化时保存
  const handleLineHtmlChange = useCallback((blockId: string, lineId: string, html: string) => {
    onUpdateLineText(blockId, lineId, html);
  }, [onUpdateLineText]);

  // 点击工具栏按钮：恢复选中 → execCommand 格式化 → 读取 innerHTML → 持久化
  const handleFormat = useCallback((format: TextFormatAction) => {
    const sel = window.getSelection();

    // 处理插入图片
    if (format === "insert-image") {
      const url = prompt("请输入图片 URL：");
      if (!url) return;
      // 在当前位置插入图片
      if (lastRangeRef.current) {
        sel?.removeAllRanges();
        sel?.addRange(lastRangeRef.current);
      }
      document.execCommand("insertImage", false, url);
      // 保存修改
      saveEditedLineHtml();
      return;
    }

    // 处理插入表格
    if (format === "insert-table") {
      const cols = prompt("列数：", "3");
      const rows = prompt("行数：", "3");
      if (!cols || !rows) return;
      if (lastRangeRef.current) {
        sel?.removeAllRanges();
        sel?.addRange(lastRangeRef.current);
      }
      let tableHtml = '<table border="1" style="width:100%;border-collapse:collapse"><tbody>';
      for (let r = 0; r < parseInt(rows); r++) {
        tableHtml += '<tr>';
        for (let c = 0; c < parseInt(cols); c++) {
          tableHtml += `<td style="border:1px solid #ccc;padding:4px;min-width:40px">&nbsp;</td>`;
        }
        tableHtml += '</tr>';
      }
      tableHtml += '</tbody></table>';
      document.execCommand("insertHTML", false, tableHtml);
      saveEditedLineHtml();
      return;
    }

    // 恢复选中的 range
    if (!lastRangeRef.current) {
      if (!sel || sel.toString().trim().length === 0) return;
    } else {
      sel?.removeAllRanges();
      sel?.addRange(lastRangeRef.current);
    }

    // 对选中部分应用格式
    if (format === "bold") document.execCommand("bold", false);
    else if (format === "italic") document.execCommand("italic", false);
    else if (format === "underline") document.execCommand("underline", false);
    else if (format === "strikethrough") document.execCommand("strikeThrough", false);
    else if (format === "align-left") document.execCommand("justifyLeft", false);
    else if (format === "align-center") document.execCommand("justifyCenter", false);
    else if (format === "align-right") document.execCommand("justifyRight", false);
    else if (format === "highlight") {
      // 切换高亮：检查选中区域是否已经有黄色背景
      const isHighlighted = sel && sel.anchorNode?.parentElement?.closest?.("[style*='background']");
      document.execCommand("backColor", false, "#fef08a");
    }

    // 保存修改后的 HTML
    saveEditedLineHtml();
  }, [onUpdateLineText, onFormatLine]);

  // 从当前选中区域的父元素找到 data-line-id 并保存内容
  const saveEditedLineHtml = useCallback(() => {
    const sel = window.getSelection();
    if (!sel || !sel.anchorNode) return;
    let el = sel.anchorNode.nodeType === Node.ELEMENT_NODE
      ? sel.anchorNode as HTMLElement
      : sel.anchorNode.parentElement;
    while (el && !el.dataset.lineId) el = el.parentElement;
    if (el && el.dataset.blockId && el.dataset.lineId) {
      const span = el.querySelector("span");
      if (span) {
        onUpdateLineText(el.dataset.blockId, el.dataset.lineId, span.innerHTML);
      }
    }
  }, [onUpdateLineText]);

  const expandedFootnote = expandedFootnoteId ? footnotes.find((fn) => fn.id === expandedFootnoteId) || null : null;

  const handleViewFootnote = useCallback((ref: string) => {
    const footnote = footnotes.find((fn) => fn.refNumber === ref);
    if (footnote) onToggleFootnote(footnote.id);
  }, [footnotes, onToggleFootnote]);

  const handleDownload = () => {
    const btn = document.createElement("a");
    btn.href = "#"; btn.download = "document.md"; btn.click();
  };
  const handleShare = () => {
    if (navigator.share) { navigator.share({ title: "GreenBean Document", text: "Share my course analysis" }).catch(() => {}); }
  };

  return (
    <div className="flex flex-col h-full">
      {/* 顶部栏 */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-black/5 dark:border-white/10 bg-white/50 dark:bg-white/[0.02]">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 tracking-tight">{t("wsDocViewer")}</h2>
          {selectedSectionId && <span className="text-[11px] text-neutral-400 dark:text-neutral-500 bg-black/5 dark:bg-white/10 px-2 py-0.5 rounded-full">{t("wsFiltered")}</span>}
        </div>
        <div className="flex items-center gap-1.5">
          <button onClick={handleDownload} className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-black/10 dark:hover:bg-white/10 text-neutral-400 dark:text-neutral-500 transition" title={t("wsDownload")}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
          </button>
          <button onClick={handleShare} className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-black/10 dark:hover:bg-white/10 text-neutral-400 dark:text-neutral-500 transition" title={t("wsShare")}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" /></svg>
          </button>
          <span className="text-[11px] text-neutral-400 dark:text-neutral-500 ml-1">{filteredBlocks.length} {t("wsSections")}</span>
        </div>
      </div>

      {/* Word风格工具栏 — 启用状态依赖选中文字 */}
      <DocumentToolbar selectedLineId={hasSelection ? "selected" : null} onFormat={handleFormat} />

      {/* Word风格文档内容 */}
      <div
        ref={viewerRef}
        className="flex-1 overflow-y-auto px-6 md:px-10 py-4 scrollbar-hide"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {showEmptyState ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-2xl bg-black/5 dark:bg-white/10 flex items-center justify-center mb-4">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" className="text-neutral-400 dark:text-neutral-500">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
              </svg>
            </div>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 font-medium">{t("wsSelectSection")}</p>
            <p className="text-xs text-neutral-400 dark:text-neutral-500 mt-1">{t("wsClickHint")}</p>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto">
            {filteredBlocks.map((block, idx) => (
              <div key={block.id}>
                {idx > 0 && <hr className="my-4 border-black/5 dark:border-white/10" />}
                <h3 className="text-base font-semibold text-neutral-800 dark:text-neutral-200 mb-3 tracking-tight">{block.title}</h3>
                <BlockContent block={block} onViewFootnote={handleViewFootnote} onLineHtmlChange={handleLineHtmlChange} />
              </div>
            ))}
          </div>
        )}
      </div>

      {showSelectionMenu && selectionMenuPos && currentSelection && (
        <SelectionMenu pos={selectionMenuPos} onQuote={() => { onQuoteSelection(); onShowSelectionMenu(false); }} onClose={() => onShowSelectionMenu(false)} />
      )}

      <AnimatePresence>
        {expandedFootnote && <FootnotePanel footnote={expandedFootnote} onClose={() => onToggleFootnote(expandedFootnote.id)} />}
      </AnimatePresence>
    </div>
  );
}

export default DocumentViewer;
import { useRef, useCallback, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import DocumentToolbar from "../shared/DocumentToolbar";
import type { DocumentViewerProps } from "../../type";
import type { ContentLine, ContentBlock, FootnoteReference } from "../../../../types/section";

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

/** 可编辑的文本行 */
function EditableText({ text, onBlur }: { text: string; onBlur: (newText: string) => void }) {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (ref.current && ref.current.textContent !== text) {
      ref.current.textContent = text;
    }
  }, [text]);
  return (
    <span
      ref={ref}
      contentEditable
      suppressContentEditableWarning
      onBlur={(e) => {
        const val = e.currentTarget.textContent ?? "";
        if (val !== text) onBlur(val);
      }}
      className="outline-none cursor-text"
    />
  );
}

/** 可交互的内容行：支持选中部分文字 + 内联编辑 */
function ContentLineRender({ line, blockId, onViewFootnote, onLineHtmlChange }: {
  line: ContentLine;
  blockId: string;
  onViewFootnote?: (ref: string) => void;
  onLineHtmlChange?: (blockId: string, lineId: string, html: string) => void;
}) {
  const spanRef = useRef<HTMLSpanElement>(null);

  const handleFootnoteClick = useCallback((e: React.MouseEvent, ref: string) => {
    e.stopPropagation();
    e.preventDefault();
    if (onViewFootnote) onViewFootnote(ref);
  }, [onViewFootnote]);

  // contentEditable 失去焦点时保存文本内容
  const handleBlur = useCallback(() => {
    if (spanRef.current && onLineHtmlChange) {
      const text = spanRef.current.textContent ?? "";
      if (text !== line.text) {
        onLineHtmlChange(blockId, line.id, text);
      }
    }
  }, [blockId, line.id, line.text, onLineHtmlChange]);

  // 同步外部 line.text 变化到 contentEditable（仅在内容确实不同时）
  useEffect(() => {
    if (spanRef.current && spanRef.current.textContent !== line.text) {
      spanRef.current.textContent = line.text;
    }
  }, [line.text]);

  return (
    <div
      data-block-id={blockId}
      data-line-id={line.id}
      className={`px-1 py-0.5 rounded-sm transition-colors ${
        line.highlighted
          ? "bg-yellow-200/60"
          : "hover:bg-black/[0.02]"
      } ${line.type === "code" ? "font-mono text-sm bg-black/5 rounded px-2 py-1" : ""}`}
    >
      <span
        ref={spanRef}
        contentEditable={true}
        suppressContentEditableWarning={true}
        onBlur={handleBlur}
        className={`outline-none cursor-text ${getLineStyle(line)}`}
        style={{ color: line.color || undefined, backgroundColor: line.highlighted ? "rgba(254,240,138,0.4)" : undefined }}
      />
      {line.footnoteRef && (
        <button
          onClick={(e) => handleFootnoteClick(e, line.footnoteRef!)}
          className="inline-flex items-center justify-center w-4 h-4 ml-1 text-[10px] font-medium text-blue-600 bg-blue-100 rounded-full cursor-pointer hover:bg-blue-200 transition-colors align-super flex-shrink-0"
          title="点击查看原文引用"
        >
          {line.footnoteRef}
        </button>
      )}
    </div>
  );
}

/** 可编辑的表格块 */
function TableBlock({ block, onLineHtmlChange }: { block: ContentBlock; onLineHtmlChange?: (blockId: string, lineId: string, html: string) => void }) {
  if (!block.tableData) return null;
  const { headers, rows } = block.tableData;
  const handleCellEdit = (rowId: string, cellIdx: number, text: string) => {
    onLineHtmlChange?.(block.id, `${rowId}-cell-${cellIdx}`, text);
  };
  return (
    <div className="overflow-x-auto my-3">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-black/5">
            {headers.map((h, i) => (
              <th key={i} className="px-4 py-2 text-left font-semibold text-neutral-700 border-b border-black/10 text-xs">
                <EditableText text={h} onBlur={(val) => {
                  block.tableData!.headers[i] = val;
                  onLineHtmlChange?.(block.id, `header-${i}`, val);
                }} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-black/5">
              {row.cells.map((cell, i) => (
                <td key={i} className="px-4 py-2 text-neutral-600 text-xs">
                  <EditableText text={cell} onBlur={(val) => handleCellEdit(row.id, i, val)} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** 可编辑的图片块（含可编辑的图例/标题） */
function ImageBlock({ block, onLineHtmlChange }: { block: ContentBlock; onLineHtmlChange?: (blockId: string, lineId: string, html: string) => void }) {
  return (
    <div className="flex flex-col items-center my-4">
      <div className={`w-full max-w-md aspect-video rounded-lg ${block.imageUrl ? "" : "bg-gradient-to-br from-blue-100 to-purple-100"} flex items-center justify-center border border-black/5`}>
        {block.imageUrl ? (
          <img src={block.imageUrl} alt={block.imageCaption || block.title} className="w-full h-full object-contain rounded-lg" />
        ) : (
          <div className="text-center p-6">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="text-blue-400 mx-auto mb-2">
              <rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" />
            </svg>
            <p className="text-xs text-neutral-400">Chart</p>
          </div>
        )}
      </div>
      {block.imageCaption && (
        <p className="mt-1.5 text-xs text-neutral-500 text-center italic">
          <EditableText text={block.imageCaption} onBlur={(val) => {
            onLineHtmlChange?.(block.id, `caption-${block.id}`, val);
          }} />
        </p>
      )}
    </div>
  );
}

function SelectionMenu({ pos, onQuote, onClose }: { pos: { x: number; y: number }; onQuote: () => void; onClose: () => void }) {
  return (<><div className="fixed inset-0 z-40" onClick={onClose} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClose(); }} tabIndex={0} role="button" aria-label="Close selection menu" />
    <div className="fixed z-50 bg-white rounded-xl shadow-xl border border-black/10 py-1 min-w-[140px]" style={{ left: pos.x, top: pos.y }}>
      <button onClick={onQuote} className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-neutral-700 hover:bg-black/5 transition">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
        引用此段询问 AI
      </button>
    </div>
  </>);
}

function FootnotePanel({ footnote, onClose }: { footnote: FootnoteReference; onClose: () => void }) {
  return (
    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="border-t border-black/5 overflow-hidden">
      <div className="px-4 py-3 bg-blue-50/50">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center justify-center w-5 h-5 text-[10px] font-bold text-blue-600 bg-blue-100 rounded-full">{footnote.refNumber}</span>
              <span className="text-[11px] text-neutral-400 font-medium">{footnote.sourceDesc}</span>
            </div>
            <p className="text-sm text-neutral-600 leading-relaxed">{footnote.sourceText}</p>
          </div>
          <button onClick={onClose} className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center hover:bg-black/10 transition">
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
  if (block.contentType === "table") return <TableBlock block={block} onLineHtmlChange={onLineHtmlChange} />;
  if (block.contentType === "image") return <ImageBlock block={block} onLineHtmlChange={onLineHtmlChange} />;
  return (
    <div className="space-y-0.5">
      {(block.lines || []).map((line) => (
        <ContentLineRender key={line.id} line={line} blockId={block.id} onViewFootnote={onViewFootnote} onLineHtmlChange={onLineHtmlChange} />
      ))}
    </div>
  );
}

function DocumentViewer({
  contentBlocks, selectedSectionId, pendingFileName, footnotes, expandedFootnoteId,
  showSelectionMenu, selectionMenuPos,
  onUpdateLineText, onToggleFootnote,
  onShowSelectionMenu, onQuoteSelection,
}: DocumentViewerProps) {
  const viewerRef = useRef<HTMLDivElement>(null);

  const filteredBlocks = selectedSectionId
    ? contentBlocks.filter((block) => block.sectionId === selectedSectionId)
    : [];
  const showEmptyState = !selectedSectionId;

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

  // 工具栏格式操作 — 通过 document.execCommand 在 mousedown 阶段执行
  const expandedFootnote = expandedFootnoteId ? footnotes.find((fn) => fn.id === expandedFootnoteId) || null : null;

  const handleViewFootnote = useCallback((ref: string) => {
    const footnote = footnotes.find((fn) => fn.refNumber === ref);
    if (footnote) onToggleFootnote(footnote.id);
  }, [footnotes, onToggleFootnote]);

  const handleDownload = () => {
    const btn = document.createElement("a");
    btn.href = "#"; btn.download = "document.md";
    document.body.appendChild(btn);
    btn.click();
    document.body.removeChild(btn);
  };
  const handleShare = () => {
    if (navigator.share) {
      navigator.share({ title: "GreenBean Document", text: "Share my course analysis" }).catch((_err: unknown) => {
        // User cancelled share or share failed - this is expected
      });
    }
  };

  const showSelectionMenuVisible = showSelectionMenu && selectionMenuPos;

  return (
    <div className="flex flex-col h-full">
      {/* 顶部栏：文档解析永远横向排列且保证最小显示宽度，按钮必要时移至第二行 */}
      <div className="flex flex-wrap items-center px-4 py-2 border-b border-black/5 bg-white/50 gap-x-1">
        <h2 className="text-sm font-semibold text-neutral-700 tracking-tight whitespace-nowrap flex-shrink-0">文档解析</h2>
        <div className="flex items-center gap-1.5 flex-shrink-0 ml-auto">
          <button onClick={handleDownload}
            className="cursor-pointer w-7 h-7 rounded-md flex items-center justify-center hover:bg-black/10 text-neutral-400 transition"
            title="下载">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
          </button>
          <button onClick={handleShare}
            className="cursor-pointer w-7 h-7 rounded-md flex items-center justify-center hover:bg-black/10 text-neutral-400 transition"
            title="分享">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" /></svg>
          </button>
        </div>
      </div>

      {/* Word风格工具栏 — 启用状态依赖选中文字 */}
      <DocumentToolbar selectedLineId={hasSelection ? "selected" : null} />

      {/* Word风格文档内容 — 容器过窄时不换行，允许用户横向滚动查看完整文字 */}
      <div
        ref={viewerRef}
        className="flex-1 overflow-y-auto overflow-x-auto px-6 md:px-10 py-4 scrollbar-hide"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {showEmptyState ? (
          <div className="inline-block pt-16 pl-6">
            <div className="w-16 h-16 rounded-2xl bg-black/5 flex items-center justify-center mb-4">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" className="text-neutral-400">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
              </svg>
            </div>
            <p className="text-sm text-neutral-500 font-medium">
              {pendingFileName ? `《${pendingFileName}》已上传，等待解析` : "从左侧上传一份文档开始"}
            </p>
            <p className="text-xs text-neutral-400 mt-1">
              {pendingFileName ? "解析能力尚未接入，刷新后需要重新上传" : "支持 PDF、Word、PPT、图片、TXT 和 Markdown"}
            </p>
          </div>
        ) : (
          <div className="min-w-max" style={{ minWidth: "max-content" }}>
            <div className="max-w-3xl mx-auto">
              {filteredBlocks.map((block, idx) => (
                <div key={block.id}>
                  {idx > 0 && <hr className="my-4 border-black/5" />}
                  <h3 className="text-base font-semibold text-neutral-800 mb-3 tracking-tight">
                    <EditableText text={block.title} onBlur={(val) => {
                      onUpdateLineText(block.id, `title-${block.id}`, val);
                    }} />
                  </h3>
                  <BlockContent block={block} onViewFootnote={handleViewFootnote} onLineHtmlChange={handleLineHtmlChange} />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <AnimatePresence>
        {expandedFootnote && <FootnotePanel footnote={expandedFootnote} onClose={() => onToggleFootnote(expandedFootnote.id)} />}
      </AnimatePresence>

      {showSelectionMenuVisible && (
        <SelectionMenu
          pos={selectionMenuPos!}
          onQuote={onQuoteSelection}
          onClose={() => onShowSelectionMenu(false)}
        />
      )}
    </div>
  );
}

export default DocumentViewer;

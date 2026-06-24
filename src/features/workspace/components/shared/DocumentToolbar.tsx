import type { TextFormatAction } from "../../type";

/** Word 风格文档工具栏按钮 */
interface ToolbarButton {
  icon: React.ReactNode;
  title: string;
  action: TextFormatAction;
}

const TOOLBAR_BUTTONS: ToolbarButton[] = [
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><text x="5" y="16" fontWeight="bold" fontSize="14" fill="currentColor">B</text></svg>,
    title: "加粗",
    action: "bold",
  },
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><text x="5" y="16" fontStyle="italic" fontSize="14" fill="currentColor">I</text></svg>,
    title: "斜体",
    action: "italic",
  },
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 18 L18 6" /><text x="5" y="16" textDecoration="underline" fontSize="14" fill="currentColor">U</text></svg>,
    title: "下划线",
    action: "underline",
  },
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="4" y1="12" x2="20" y2="12" /><text x="5" y="16" textDecoration="line-through" fontSize="14" fill="currentColor">S</text></svg>,
    title: "删除线",
    action: "strikethrough",
  },
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" fill="#fef08a" stroke="#facc15" /><text x="7" y="16" fontSize="12" fill="#92400e" fontWeight="bold">A</text></svg>,
    title: "高亮",
    action: "highlight",
  },
];

const INSERT_BUTTONS: ToolbarButton[] = [
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" /></svg>,
    title: "插入图片",
    action: "insert-image",
  },
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><rect x="3" y="3" width="18" height="18" rx="2" /><line x1="3" y1="9" x2="21" y2="9" /><line x1="9" y1="21" x2="9" y2="9" /></svg>,
    title: "插入表格",
    action: "insert-table",
  },
];

const ALIGN_BUTTONS: ToolbarButton[] = [
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><line x1="4" y1="6" x2="20" y2="6" /><line x1="4" y1="10" x2="14" y2="10" /><line x1="4" y1="14" x2="18" y2="14" /><line x1="4" y1="18" x2="10" y2="18" /></svg>,
    title: "左对齐",
    action: "align-left",
  },
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><line x1="4" y1="6" x2="20" y2="6" /><line x1="6" y1="10" x2="18" y2="10" /><line x1="4" y1="14" x2="20" y2="14" /><line x1="8" y1="18" x2="16" y2="18" /></svg>,
    title: "居中",
    action: "align-center",
  },
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><line x1="4" y1="6" x2="20" y2="6" /><line x1="10" y1="10" x2="20" y2="10" /><line x1="6" y1="14" x2="20" y2="14" /><line x1="14" y1="18" x2="20" y2="18" /></svg>,
    title: "右对齐",
    action: "align-right",
  },
];

interface DocumentToolbarProps {
  selectedLineId: string | null;
  onFormat?: (action: TextFormatAction) => void;
}

/** 选中文字用指定标签包裹（直接 DOM 操作，保留选中高亮） */
export function execLocalFormat(action: TextFormatAction): boolean {
  const sel = window.getSelection();
  if (!sel || !sel.rangeCount || sel.toString().trim().length === 0) return false;
  const range = sel.getRangeAt(0);
  const text = range.toString();
  if (!text.trim()) return false;

  if (action === "bold") {
    const b = document.createElement("b");
    b.textContent = text;
    range.deleteContents(); range.insertNode(b);
    const nr = document.createRange(); nr.selectNodeContents(b);
    sel.removeAllRanges(); sel.addRange(nr);
    b.dispatchEvent(new Event("input", { bubbles: true }));
    return true;
  }
  if (action === "italic") {
    const i = document.createElement("i");
    i.textContent = text;
    range.deleteContents(); range.insertNode(i);
    const nr = document.createRange(); nr.selectNodeContents(i);
    sel.removeAllRanges(); sel.addRange(nr);
    i.dispatchEvent(new Event("input", { bubbles: true }));
    return true;
  }
  if (action === "underline") {
    const u = document.createElement("u");
    u.textContent = text;
    range.deleteContents(); range.insertNode(u);
    const nr = document.createRange(); nr.selectNodeContents(u);
    sel.removeAllRanges(); sel.addRange(nr);
    u.dispatchEvent(new Event("input", { bubbles: true }));
    return true;
  }
  if (action === "strikethrough") {
    const s = document.createElement("s");
    s.textContent = text;
    range.deleteContents(); range.insertNode(s);
    const nr = document.createRange(); nr.selectNodeContents(s);
    sel.removeAllRanges(); sel.addRange(nr);
    s.dispatchEvent(new Event("input", { bubbles: true }));
    return true;
  }
  if (action === "highlight") {
    const parentEl = range.commonAncestorContainer.nodeType === Node.ELEMENT_NODE
      ? range.commonAncestorContainer as HTMLElement
      : range.commonAncestorContainer.parentElement;
    const isHighlighted = parentEl?.closest?.("[style*='background']") !== null;
    const span = document.createElement("span");
    span.textContent = text;
    if (!isHighlighted) span.style.backgroundColor = "#fef08a";
    range.deleteContents(); range.insertNode(span);
    const nr = document.createRange(); nr.selectNodeContents(span);
    sel.removeAllRanges(); sel.addRange(nr);
    span.dispatchEvent(new Event("input", { bubbles: true }));
    return true;
  }
  // 对齐：设置行容器（data-line-id 的父 div）的 textAlign
  if (action.startsWith("align-")) {
    let el = range.startContainer.nodeType === Node.ELEMENT_NODE
      ? range.startContainer as HTMLElement
      : range.startContainer.parentElement;
    // 找到 data-line-id 的父 div（块级容器）
    while (el && !el.dataset?.lineId) el = el.parentElement;
    if (el) {
      el.style.textAlign = action.replace("align-", "");
      el.dispatchEvent(new Event("input", { bubbles: true }));
    }
    return true;
  }
  return false;
}

/** 通用渲染按钮的辅助函数，alwaysEnabled 表示该按钮不受选中状态影响（常亮） */
function renderToolbarButton(btn: ToolbarButton, enabled: boolean, onFormat?: (action: TextFormatAction) => void, alwaysEnabled = false) {
  const active = alwaysEnabled || enabled;
  const handleMouseDown = (e: React.MouseEvent) => {
    if (active) {
      if (btn.action === "insert-image" || btn.action === "insert-table") {
        onFormat?.(btn.action);
      } else if (enabled) {
        execLocalFormat(btn.action);
      }
    }
    e.preventDefault();
  };

  return (
    <button
      key={btn.action}
      onMouseDown={handleMouseDown}
      disabled={!active}
      title={btn.title}
      className={`w-7 h-7 rounded-md flex items-center justify-center text-neutral-500 transition-colors ${
        active
          ? "cursor-pointer hover:bg-black/10 hover:text-neutral-700"
          : "opacity-40 cursor-not-allowed"
      }`}
    >
      {btn.icon}
    </button>
  );
}

function DocumentToolbar({ selectedLineId, onFormat }: DocumentToolbarProps) {
  const enabled = !!selectedLineId;
  return (
    <div className="flex items-center gap-1 px-3 py-1.5 bg-white/80 border-b border-black/5 overflow-x-auto" style={{ scrollbarWidth: "none" }}>
      <div className="flex items-center gap-0.5 pr-2 border-r border-black/10">
        {TOOLBAR_BUTTONS.map((btn) => renderToolbarButton(btn, enabled, onFormat))}
      </div>
      <div className="flex items-center gap-0.5 pl-2 pr-2 border-r border-black/10">
        {INSERT_BUTTONS.map((btn) => renderToolbarButton(btn, enabled, onFormat, true))}
      </div>
      <div className="flex items-center gap-0.5 pl-1">
        {ALIGN_BUTTONS.map((btn) => renderToolbarButton(btn, enabled, onFormat))}
      </div>
    </div>
  );
}

export default DocumentToolbar;

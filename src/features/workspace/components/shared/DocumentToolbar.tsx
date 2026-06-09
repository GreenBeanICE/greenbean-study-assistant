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
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12" /><text x="5" y="16" fontSize="14" fill="currentColor">U</text></svg>,
    title: "下划线",
    action: "underline",
  },
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12" /></svg>,
    title: "删除线",
    action: "strikethrough",
  },
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="3" y="8" width="18" height="2" rx="1" /><rect x="3" y="14" width="18" height="2" rx="1" /></svg>,
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
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /><line x1="3" y1="14" x2="21" y2="14" /><line x1="3" y1="18" x2="21" y2="18" /></svg>,
    title: "左对齐",
    action: "align-left",
  },
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><line x1="3" y1="6" x2="21" y2="6" /><line x1="6" y1="10" x2="18" y2="10" /><line x1="3" y1="14" x2="21" y2="14" /><line x1="6" y1="18" x2="18" y2="18" /></svg>,
    title: "居中",
    action: "align-center",
  },
  {
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /><line x1="3" y1="14" x2="21" y2="14" /><line x1="3" y1="18" x2="21" y2="18" /></svg>,
    title: "右对齐",
    action: "align-right",
  },
];

interface DocumentToolbarProps {
  selectedLineId: string | null;
  onFormat: (action: TextFormatAction) => void;
}

function DocumentToolbar({ selectedLineId, onFormat }: DocumentToolbarProps) {
  return (
    <div className="flex items-center gap-1 px-3 py-1.5 bg-white/80 dark:bg-white/5 border-b border-black/5 dark:border-white/10 overflow-x-auto" style={{ scrollbarWidth: "none" }}>
      <div className="flex items-center gap-0.5 pr-2 border-r border-black/10 dark:border-white/10">
        {TOOLBAR_BUTTONS.map((btn) => (
          <button
            key={btn.action}
            onClick={() => onFormat(btn.action)}
            disabled={!selectedLineId}
            title={btn.title}
            className={`w-7 h-7 rounded-md flex items-center justify-center text-neutral-500 dark:text-neutral-400 transition-colors ${
              selectedLineId
                ? "hover:bg-black/10 dark:hover:bg-white/10 hover:text-neutral-700 dark:hover:text-neutral-200"
                : "opacity-40 cursor-not-allowed"
            }`}
          >
            {btn.icon}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-0.5 pl-2 pr-2 border-r border-black/10 dark:border-white/10">
        {INSERT_BUTTONS.map((btn) => (
          <button
            key={btn.action}
            onClick={() => onFormat(btn.action)}
            disabled={!selectedLineId}
            title={btn.title}
            className={`w-7 h-7 rounded-md flex items-center justify-center text-neutral-500 dark:text-neutral-400 transition-colors ${
              selectedLineId
                ? "hover:bg-black/10 dark:hover:bg-white/10 hover:text-neutral-700 dark:hover:text-neutral-200"
                : "opacity-40 cursor-not-allowed"
            }`}
          >
            {btn.icon}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-0.5 pl-1">
        {ALIGN_BUTTONS.map((btn) => (
          <button
            key={btn.action}
            onClick={() => onFormat(btn.action)}
            disabled={!selectedLineId}
            title={btn.title}
            className={`w-7 h-7 rounded-md flex items-center justify-center text-neutral-500 dark:text-neutral-400 transition-colors ${
              selectedLineId
                ? "hover:bg-black/10 dark:hover:bg-white/10 hover:text-neutral-700 dark:hover:text-neutral-200"
                : "opacity-40 cursor-not-allowed"
            }`}
          >
            {btn.icon}
          </button>
        ))}
      </div>
    </div>
  );
}

export default DocumentToolbar;
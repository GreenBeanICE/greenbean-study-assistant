import { motion, AnimatePresence } from "framer-motion";
import type { SectionTreeProps } from "../../type";
import type { SectionNode } from "../../../../types/section";

function formatSectionLocation(node: SectionNode): string | null {
  if (node.startPage == null && node.endPage == null) {
    return null;
  }

  if (
    node.startPage != null
    && node.endPage != null
    && node.startPage !== node.endPage
  ) {
    return `${node.startPage}-${node.endPage} 页`;
  }

  const singlePage = node.startPage ?? node.endPage;
  return singlePage != null ? `第 ${singlePage} 页` : null;
}

function TreeNode({ node, depth = 0, selectedSectionId, onSelect, onToggle }: {
  node: SectionNode; depth?: number; selectedSectionId: string | null;
  onSelect: (sectionId: string) => void; onToggle: (sectionId: string) => void;
}) {
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedSectionId === node.id;
  const isExpanded = node.expanded ?? true;
  const location = formatSectionLocation(node);

  return (
    <div>
      <button onClick={() => { onSelect(node.id); if (hasChildren) onToggle(node.id); }}
        className={`cursor-pointer w-full flex items-center gap-2 px-3 py-2 text-left rounded-xl transition-all duration-200 ${
          isSelected ? "bg-neutral-200 text-neutral-800" : "text-neutral-700 hover:bg-black/5"
        }`} style={{ paddingLeft: `${12 + depth * 16}px` }}>
        {hasChildren ? (
          <span onClick={(e) => { e.stopPropagation(); onToggle(node.id); }} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.stopPropagation(); onToggle(node.id); } }} tabIndex={0} role="button" aria-label={isExpanded ? "Collapse section" : "Expand section"}
            className={`flex-shrink-0 w-4 h-4 flex items-center justify-center transition-transform duration-200 ${isExpanded ? "rotate-90" : ""}`}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6" /></svg>
          </span>
        ) : <span className="flex-shrink-0 w-4" />}
        <span className="min-w-0 flex-1">
          <span className="block font-medium truncate text-[13px]">{node.index ? `${node.index} ` : ""}{node.title}</span>
          {location ? <span className="block text-[11px] text-neutral-400 mt-0.5">{location}</span> : null}
        </span>
      </button>
      <AnimatePresence>{hasChildren && isExpanded && (
        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
          {node.children!.map((child) => <TreeNode key={child.id} node={child} depth={depth + 1} selectedSectionId={selectedSectionId} onSelect={onSelect} onToggle={onToggle} />)}
        </motion.div>
      )}</AnimatePresence>
    </div>
  );
}

function SectionTree({ sections, selectedSectionId, onSelect, onToggle, onBack, title: customTitle }: SectionTreeProps & { onBack?: () => void; title?: string }) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-black/5">
        {onBack && (
          <button onClick={onBack}
            className="cursor-pointer w-6 h-6 rounded-md flex items-center justify-center hover:bg-black/10 text-neutral-400 transition flex-shrink-0"
            title="返回文件列表">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
          </button>
        )}
        <h2 className="text-sm font-semibold text-neutral-700 tracking-tight truncate flex-1">{customTitle || "章节导航"}</h2>
        <span className="text-[11px] text-neutral-400 font-medium flex-shrink-0">{sections.length} 个章节</span>
      </div>
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5 scrollbar-hide" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
        {sections.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-12 h-12 rounded-2xl bg-black/5 flex items-center justify-center mb-3">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" className="text-neutral-400">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <p className="text-sm text-neutral-400">暂无章节数据</p>
            <p className="text-xs text-neutral-300 mt-1">请先上传并解析文档</p>
          </div>
        ) : sections.map((node) => <TreeNode key={node.id} node={node} selectedSectionId={selectedSectionId} onSelect={onSelect} onToggle={onToggle} />)}
      </div>
    </div>
  );
}

export default SectionTree;

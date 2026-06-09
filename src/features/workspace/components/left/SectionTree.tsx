import { useI18n } from "../../../../lib/i18n";
import { motion, AnimatePresence } from "framer-motion";
import type { SectionTreeProps } from "../../type";
import type { SectionNode } from "../../../../types/section";

function TreeNode({ node, depth = 0, selectedSectionId, onSelect, onToggle }: {
  node: SectionNode; depth?: number; selectedSectionId: string | null;
  onSelect: (sectionId: string) => void; onToggle: (sectionId: string) => void;
}) {
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedSectionId === node.id;
  const isExpanded = node.expanded ?? true;

  return (
    <div>
      <button onClick={() => { onSelect(node.id); if (hasChildren) onToggle(node.id); }}
        className={`w-full flex items-center gap-2 px-3 py-2 text-left rounded-xl transition-all duration-200 ${
          isSelected ? "bg-black text-white dark:bg-white dark:text-black shadow-md" : "text-neutral-700 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/10"
        }`} style={{ paddingLeft: `${12 + depth * 16}px` }}>
        {hasChildren ? (
          <span onClick={(e) => { e.stopPropagation(); onToggle(node.id); }}
            className={`flex-shrink-0 w-4 h-4 flex items-center justify-center transition-transform duration-200 ${isExpanded ? "rotate-90" : ""}`}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6" /></svg>
          </span>
        ) : <span className="flex-shrink-0 w-4" />}
        <span className="text-sm font-medium truncate">{node.index ? `${node.index} ` : ""}{node.title}</span>
      </button>
      <AnimatePresence>{hasChildren && isExpanded && (
        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
          {node.children!.map((child) => <TreeNode key={child.id} node={child} depth={depth + 1} selectedSectionId={selectedSectionId} onSelect={onSelect} onToggle={onToggle} />)}
        </motion.div>
      )}</AnimatePresence>
    </div>
  );
}

function SectionTree({ sections, selectedSectionId, onSelect, onToggle }: SectionTreeProps) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-4 border-b border-black/5 dark:border-white/10">
        <h2 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 tracking-tight">{t("wsSectionNav")}</h2>
        <span className="text-[11px] text-neutral-400 dark:text-neutral-500 font-medium">{sections.length} {t("wsSections")}</span>
      </div>
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5 scrollbar-hide" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
        {sections.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-12 h-12 rounded-2xl bg-black/5 dark:bg-white/10 flex items-center justify-center mb-3">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" className="text-neutral-400 dark:text-neutral-500">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <p className="text-sm text-neutral-400 dark:text-neutral-500">{t("wsNoSections")}</p>
            <p className="text-xs text-neutral-300 dark:text-neutral-600 mt-1">{t("wsUploadHint")}</p>
          </div>
        ) : sections.map((node) => <TreeNode key={node.id} node={node} selectedSectionId={selectedSectionId} onSelect={onSelect} onToggle={onToggle} />)}
      </div>
    </div>
  );
}

export default SectionTree;
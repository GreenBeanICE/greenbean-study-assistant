import type { DocumentUnit } from "../../../../types/document";

interface RawTextPanelProps {
  units: DocumentUnit[];
  selectedUnitId?: string | null;
  onUnitClick?: (unitId: string) => void;
}

function RawTextPanel({ units, selectedUnitId, onUnitClick }: RawTextPanelProps) {
  if (units.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-4">
        <div className="w-12 h-12 rounded-2xl bg-black/5 flex items-center justify-center mb-3">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" className="text-neutral-400">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
          </svg>
        </div>
        <p className="text-sm text-neutral-400">暂无原文数据</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto px-4 py-4 scrollbar-hide" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
      {units.map((unit) => {
        const isSelected = selectedUnitId === unit.id;
        const pageLabel = unit.page_number != null ? `第 ${unit.page_number} 页` : `单元 ${unit.sequence_index + 1}`;

        return (
          <div
            key={unit.id}
            data-unit-id={unit.id}
            onClick={() => onUnitClick?.(unit.id)}
            className={`mb-4 p-3 rounded-lg cursor-pointer transition-colors ${
              isSelected
                ? "bg-blue-50 border border-blue-200"
                : "hover:bg-black/[0.02]"
            }`}
          >
            <div className="text-xs font-medium text-neutral-400 mb-2">{pageLabel}</div>
            <div className="text-sm text-neutral-700 leading-relaxed whitespace-pre-wrap">
              {unit.text_content || <span className="text-neutral-300 italic">（空内容）</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default RawTextPanel;

import ProviderList from "./ProviderList";
import type { ProviderConfig, Purpose } from "../types";

interface PurposeSectionProps {
  purpose: Purpose;
  providers: ProviderConfig[];
  onAdd: () => void;
  onActivate: (id: string) => void;
  onEdit: (config: ProviderConfig) => void;
  onDelete: (id: string) => void;
}

const TITLE: Record<Purpose, string> = {
  chat: "聊天模型 (chat)",
  embedding: "向量模型 (embedding)",
};

export default function PurposeSection({
  purpose,
  providers,
  onAdd,
  onActivate,
  onEdit,
  onDelete,
}: PurposeSectionProps) {
  return (
    <section className="rounded-2xl border border-black/5 bg-white/40 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-neutral-700">{TITLE[purpose]}</h3>
        <button
          onClick={onAdd}
          className="rounded-lg bg-neutral-800 px-3 py-1 text-xs text-white hover:bg-neutral-700"
        >
          + 新增
        </button>
      </div>
      {purpose === "embedding" && (
        <p className="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
          切换向量模型后，已有索引可能需要重建。
        </p>
      )}
      <ProviderList
        providers={providers}
        onActivate={onActivate}
        onEdit={onEdit}
        onDelete={onDelete}
      />
    </section>
  );
}

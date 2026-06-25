import type { ProviderConfig } from "../types";

interface ProviderListProps {
  providers: ProviderConfig[];
  onActivate: (id: string) => void;
  onEdit: (config: ProviderConfig) => void;
  onDelete: (id: string) => void;
}

export default function ProviderList({ providers, onActivate, onEdit, onDelete }: ProviderListProps) {
  if (providers.length === 0) {
    return <p className="py-4 text-center text-sm text-neutral-400">暂无配置，点击「新增」添加</p>;
  }

  return (
    <ul className="space-y-2">
      {providers.map((config) => (
        <li
          key={config.id}
          className="flex items-center justify-between rounded-lg border border-black/5 bg-white/60 px-3 py-2"
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="truncate text-sm font-medium text-neutral-800">{config.display_name}</span>
              {config.is_active && (
                <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] text-emerald-700">●已激活</span>
              )}
            </div>
            <span className="text-xs text-neutral-400">{config.model_id}</span>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <button
              onClick={() => onActivate(config.id)}
              disabled={config.is_active}
              className="rounded px-2 py-1 text-xs text-emerald-700 hover:bg-emerald-50 disabled:opacity-40"
            >
              设为激活
            </button>
            <button
              onClick={() => onEdit(config)}
              className="rounded px-2 py-1 text-xs text-neutral-600 hover:bg-black/5"
            >
              编辑
            </button>
            <button
              onClick={() => onDelete(config.id)}
              className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50"
            >
              删除
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}

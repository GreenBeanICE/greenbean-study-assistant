import { useState, FormEvent } from "react";
import { motion } from "framer-motion";
import type { ProviderConfig, ProviderPayload, Purpose } from "../types";

interface ProviderFormProps {
  purpose: Purpose;
  initial?: ProviderConfig;
  onSubmit: (payload: ProviderPayload) => void;
  onClose: () => void;
}

interface FormState {
  name: string;
  api_mode: "openai-compat";
  api_key: string;
  api_host: string;
  model_id: string;
  display_name: string;
  context_window: number;
  max_output_tokens: number;
  embedding_dimension: number | "";
}

const EMPTY: FormState = {
  name: "",
  api_mode: "openai-compat",
  api_key: "",
  api_host: "",
  model_id: "",
  display_name: "",
  context_window: 65536,
  max_output_tokens: 8192,
  embedding_dimension: "",
};

export default function ProviderForm({ purpose, initial, onSubmit, onClose }: ProviderFormProps) {
  const [form, setForm] = useState<FormState>(() => {
    if (!initial) return { ...EMPTY };
    return {
      name: initial.name,
      api_mode: initial.api_mode,
      api_key: "",
      api_host: initial.api_host,
      model_id: initial.model_id,
      display_name: initial.display_name,
      context_window: initial.context_window,
      max_output_tokens: initial.max_output_tokens,
      embedding_dimension: initial.embedding_dimension ?? "",
    };
  });

  const set = (key: keyof FormState, value: string | number) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const payload: ProviderPayload = {
      name: form.name,
      api_mode: form.api_mode,
      api_key: form.api_key,
      api_host: form.api_host,
      model_id: form.model_id,
      display_name: form.display_name,
      context_window: form.context_window,
      max_output_tokens: form.max_output_tokens,
      purpose,
      ...(purpose === "embedding" && form.embedding_dimension !== ""
        ? { embedding_dimension: Number(form.embedding_dimension) }
        : {}),
    };
    onSubmit(payload);
  };

  const isEmbedding = purpose === "embedding";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-4 text-lg font-semibold text-neutral-800">
          {initial ? "编辑配置" : "新增配置"}（{isEmbedding ? "向量" : "聊天"}模型）
        </h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <Field label="内部标识" value={form.name} onChange={(v) => set("name", v)} required />
          <Field label="展示名称" value={form.display_name} onChange={(v) => set("display_name", v)} required />
          <Field label="API 主机" value={form.api_host} onChange={(v) => set("api_host", v)} required placeholder="https://api.example.com" />
          <Field label="API 密钥" type="password" value={form.api_key} onChange={(v) => set("api_key", v)} required />
          <Field label="模型 ID" value={form.model_id} onChange={(v) => set("model_id", v)} required />
          <Field label="上下文窗口" type="number" value={String(form.context_window)} onChange={(v) => set("context_window", Number(v))} />
          <Field label="最大输出 token" type="number" value={String(form.max_output_tokens)} onChange={(v) => set("max_output_tokens", Number(v))} />
          {isEmbedding && (
            <Field label="向量维度" type="number" value={String(form.embedding_dimension)} onChange={(v) => set("embedding_dimension", Number(v))} required />
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="rounded-lg px-4 py-2 text-sm text-neutral-600 hover:bg-black/5">
              取消
            </button>
            <button type="submit" className="rounded-lg bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700">
              保存
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

interface FieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
  placeholder?: string;
}

function Field({ label, value, onChange, type = "text", required, placeholder }: FieldProps) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-neutral-500">{label}</span>
      <input
        type={type}
        value={value}
        required={required}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-emerald-500"
      />
    </label>
  );
}

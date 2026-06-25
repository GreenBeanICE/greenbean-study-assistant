import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import PurposeSection from "../components/PurposeSection";
import ProviderForm from "../components/ProviderForm";
import type { ProviderConfig, ProviderPayload, Purpose } from "../types";
import {
  activateProvider,
  createProvider,
  deleteProvider,
  listProviders,
  updateProvider,
} from "../api/providerApi";

interface SettingsPageProps {
  onBack: () => void;
}

interface FormState {
  open: boolean;
  purpose: Purpose;
  editing: ProviderConfig | null;
}

export default function SettingsPage({ onBack }: SettingsPageProps) {
  const [chatProviders, setChatProviders] = useState<ProviderConfig[]>([]);
  const [embeddingProviders, setEmbeddingProviders] = useState<ProviderConfig[]>([]);
  const [form, setForm] = useState<FormState>({ open: false, purpose: "chat", editing: null });

  const refresh = useCallback(async (purpose: Purpose) => {
    const list = await listProviders(purpose);
    if (purpose === "chat") setChatProviders(list);
    else setEmbeddingProviders(list);
  }, []);

  useEffect(() => {
    void refresh("chat");
    void refresh("embedding");
  }, [refresh]);

  const openCreate = (purpose: Purpose) =>
    setForm({ open: true, purpose, editing: null });

  const openEdit = (purpose: Purpose, config: ProviderConfig) =>
    setForm({ open: true, purpose, editing: config });

  const handleSubmit = async (payload: ProviderPayload) => {
    const purpose = form.purpose;
    if (form.editing) {
      await updateProvider(form.editing.id, payload);
    } else {
      await createProvider(payload);
    }
    setForm({ open: false, purpose: "chat", editing: null });
    await refresh(purpose);
  };

  const handleActivate = async (purpose: Purpose, id: string) => {
    await activateProvider(id);
    await refresh(purpose);
  };

  const handleDelete = async (purpose: Purpose, id: string) => {
    await deleteProvider(id);
    await refresh(purpose);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="h-screen bg-[#f5f5f7] text-neutral-800"
    >
      <header className="flex items-center justify-between border-b border-black/5 bg-white/60 px-6 py-4">
        <h1 className="text-lg font-semibold">模型设置</h1>
        <button
          onClick={onBack}
          className="rounded-lg px-3 py-1.5 text-sm text-neutral-600 hover:bg-black/5"
        >
          返回工作区
        </button>
      </header>

      <main className="mx-auto mt-6 flex max-w-3xl flex-col gap-4 px-6 pb-10">
        <PurposeSection
          purpose="chat"
          providers={chatProviders}
          onAdd={() => openCreate("chat")}
          onActivate={(id) => handleActivate("chat", id)}
          onEdit={(cfg) => openEdit("chat", cfg)}
          onDelete={(id) => handleDelete("chat", id)}
        />
        <PurposeSection
          purpose="embedding"
          providers={embeddingProviders}
          onAdd={() => openCreate("embedding")}
          onActivate={(id) => handleActivate("embedding", id)}
          onEdit={(cfg) => openEdit("embedding", cfg)}
          onDelete={(id) => handleDelete("embedding", id)}
        />
      </main>

      {form.open && (
        <ProviderForm
          purpose={form.purpose}
          initial={form.editing ?? undefined}
          onSubmit={handleSubmit}
          onClose={() => setForm({ open: false, purpose: "chat", editing: null })}
        />
      )}
    </motion.div>
  );
}

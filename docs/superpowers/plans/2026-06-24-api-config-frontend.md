# API 配置（前端）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在前端新增 `src/features/settings/` 模块，提供模型 Provider 配置页（chat / embedding 分区 CRUD + 激活）、App 三态视图切换（splash / workspace / settings）、以及首启缺配置引导 Modal。

**Architecture:** 复用 `src/lib/apiClient.ts` 的 `request<T>`（已解包后端 `{code,data}`）；新增 `providerApi.ts` 薄封装照 `documentApi.ts` 模式；设置页由 `SettingsPage` 串联 `PurposeSection → ProviderList + ProviderForm`；`App.tsx` 把 `showSplash` 扩展为 `view` 三态，齿轮入口经 `WorkspacePageProps.onOpenSettings` 注入；首启在 splash 结束时并行探测 chat/embedding active。

**Tech Stack:** React 19、TypeScript、Tailwind 4、framer-motion、Vitest、Testing Library（jsdom）。

**Spec:** `docs/superpowers/specs/2026-06-24-api-config-design.md`（5.5 前端、7.2 测试、9 验收）

**约定：**
- 单文件测试运行：`npx vitest run <path>`
- 全量前端测试：`npm run test:frontend`
- 类型检查：`npx tsc --noEmit`
- 后端契约（已实现）：`GET /api/providers?purpose=`、`POST /api/providers`、`PATCH /api/providers/{id}`、`DELETE /api/providers/{id}`、`POST /api/providers/{id}/activate`、`GET /api/providers/active?purpose=`；列表/详情 Response 不含 `api_key`；activate/active 返回精简 `{id,name,display_name,model_id}`。

---

## File Structure

**新建：**
- `src/features/settings/types.ts` — `Purpose` / `ApiMode` / `ProviderConfig` / `ProviderPayload` / `ActivateResponse`
- `src/features/settings/api/providerApi.ts` — 6 个 API 方法（照 `documentApi.ts` 薄封装）
- `src/features/settings/api/providerApi.test.ts`
- `src/features/settings/components/ProviderForm.tsx` — 新增/编辑表单 Modal
- `src/features/settings/components/ProviderForm.test.tsx`
- `src/features/settings/components/ProviderList.tsx` — 配置列表（激活态 + 设为激活/编辑/删除）
- `src/features/settings/components/ProviderList.test.tsx`
- `src/features/settings/components/PurposeSection.tsx` — chat/embedding 分区容器
- `src/features/settings/components/PurposeSection.test.tsx`
- `src/features/settings/pages/SettingsPage.tsx` — 设置页主容器
- `src/features/settings/pages/SettingsPage.test.tsx`

**修改：**
- `src/App.tsx` — `view` 三态 + 首启引导
- `src/App.test.tsx` — 视图切换与引导测试
- `src/features/workspace/type.ts:116-124` — `WorkspacePageProps` 加 `onOpenSettings?`
- `src/features/workspace/pages/WorkspacePage.tsx:343-347` — 齿轮按钮接 `onClick`

**测试模式约定（全计划复用）：**
- API 测试：`vi.mock("../../../lib/apiClient", () => ({ request: vi.fn() }))`，断言 `expect(request).toHaveBeenCalledWith(path, options)`。
- 组件测试：用以下工厂函数统一 mock framer-motion（motion 退化为普通标签、AnimatePresence 透传 children）：

```tsx
// 放在每个组件测试文件顶部（import React 之后）
vi.mock("framer-motion", () => {
  const createMotionComponent = (tag: string) => {
    const Component = (props: Record<string, unknown>) => {
      const { children, ...rest } = props;
      const { initial: _i, animate: _a, exit: _e, transition: _t, whileHover: _h, whileTap: _wt, layout: _l, layoutId: _li } = rest as Record<string, unknown>;
      return React.createElement(tag, rest, children as React.ReactNode);
    };
    Component.displayName = `motion.${tag}`;
    return Component;
  };
  return {
    motion: new Proxy({}, { get: (_t, tag: string) => createMotionComponent(tag) }),
    AnimatePresence: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
  };
});
```

---

## Task 1: types + providerApi（API 层）

**Files:**
- Create: `src/features/settings/types.ts`
- Create: `src/features/settings/api/providerApi.ts`
- Create: `src/features/settings/api/providerApi.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `src/features/settings/api/providerApi.test.ts`：

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../../../lib/apiClient", () => ({ request: vi.fn() }));

import { request } from "../../../lib/apiClient";
import {
  listProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  activateProvider,
  getActiveProvider,
} from "./providerApi";
import type { ProviderPayload } from "../types";

describe("providerApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("listProviders 不传 purpose 时 GET /providers", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    await listProviders();
    expect(request).toHaveBeenCalledWith("/providers");
  });

  it("listProviders 传 purpose 时附加查询参数", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    await listProviders("chat");
    expect(request).toHaveBeenCalledWith("/providers?purpose=chat");
  });

  it("createProvider POST /providers 发送 JSON body", async () => {
    const payload: ProviderPayload = {
      name: "deepseek",
      api_mode: "openai-compat",
      api_key: "sk-x",
      api_host: "https://api.deepseek.com",
      model_id: "deepseek-chat",
      display_name: "DeepSeek",
      purpose: "chat",
    };
    (request as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "cfg-1" });
    const result = await createProvider(payload);
    expect(result).toEqual({ id: "cfg-1" });
    const [path, options] = (request as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/providers");
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body as string)).toEqual(payload);
  });

  it("updateProvider PATCH /providers/{id}", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "cfg-1" });
    await updateProvider("cfg-1", { display_name: "New" });
    const [path, options] = (request as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/providers/cfg-1");
    expect(options.method).toBe("PATCH");
  });

  it("deleteProvider DELETE /providers/{id}", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    const result = await deleteProvider("cfg-1");
    expect(result).toBe(true);
    expect(request).toHaveBeenCalledWith("/providers/cfg-1", { method: "DELETE" });
  });

  it("activateProvider POST /providers/{id}/activate", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "cfg-1" });
    await activateProvider("cfg-1");
    expect(request).toHaveBeenCalledWith("/providers/cfg-1/activate", { method: "POST" });
  });

  it("getActiveProvider GET /providers/active?purpose=", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "cfg-1" });
    await getActiveProvider("embedding");
    expect(request).toHaveBeenCalledWith("/providers/active?purpose=embedding");
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `npx vitest run src/features/settings/api/providerApi.test.ts`
Expected: FAIL — `Cannot find module './providerApi'` / `../types`

- [ ] **Step 3: 创建 types + providerApi**

创建 `src/features/settings/types.ts`：

```typescript
export type Purpose = "chat" | "embedding";
export type ApiMode = "openai-compat";

/** Provider 配置（列表/详情响应，后端已脱敏，不含 api_key）。 */
export interface ProviderConfig {
  id: string;
  name: string;
  api_mode: ApiMode;
  api_host: string;
  api_path: string;
  model_id: string;
  display_name: string;
  context_window: number;
  max_output_tokens: number;
  purpose: Purpose;
  embedding_dimension: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** 新增 / 编辑表单提交载荷。 */
export interface ProviderPayload {
  name: string;
  api_mode: ApiMode;
  api_key: string;
  api_host: string;
  api_path?: string;
  model_id: string;
  display_name: string;
  context_window?: number;
  max_output_tokens?: number;
  purpose: Purpose;
  embedding_dimension?: number | null;
}

/** 激活 / 当前激活响应。 */
export interface ActivateResponse {
  id: string;
  name: string;
  display_name: string;
  model_id: string;
}
```

创建 `src/features/settings/api/providerApi.ts`：

```typescript
/**
 * Provider 配置 API 封装 —— 对 apiClient 的薄封装。
 * 相对路径 /api/providers/... 由 vite proxy 转发到 Python 后端。
 */
import { request } from "../../../lib/apiClient";
import type {
  ActivateResponse,
  ProviderConfig,
  ProviderPayload,
  Purpose,
} from "../types";

export function listProviders(purpose?: Purpose): Promise<ProviderConfig[]> {
  const query = purpose ? `?purpose=${purpose}` : "";
  return request(`/providers${query}`);
}

export function createProvider(payload: ProviderPayload): Promise<ProviderConfig> {
  return request("/providers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateProvider(
  id: string,
  payload: Partial<ProviderPayload>,
): Promise<ProviderConfig> {
  return request(`/providers/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteProvider(id: string): Promise<boolean> {
  return request(`/providers/${id}`, { method: "DELETE" });
}

export function activateProvider(id: string): Promise<ActivateResponse> {
  return request(`/providers/${id}/activate`, { method: "POST" });
}

export function getActiveProvider(purpose: Purpose): Promise<ActivateResponse> {
  return request(`/providers/active?purpose=${purpose}`);
}
```

- [ ] **Step 4: 运行测试验证通过**

Run: `npx vitest run src/features/settings/api/providerApi.test.ts`
Expected: PASS（7 个用例）

- [ ] **Step 5: 类型检查 + 提交**

Run: `npx tsc --noEmit`
Expected: 无错误

```bash
git add src/features/settings/types.ts src/features/settings/api/providerApi.ts src/features/settings/api/providerApi.test.ts
git commit -m "feat(settings): 新增 ProviderConfig 类型与 providerApi 封装"
```

---

## Task 2: ProviderForm（新增/编辑表单 Modal）

**Files:**
- Create: `src/features/settings/components/ProviderForm.tsx`
- Create: `src/features/settings/components/ProviderForm.test.tsx`

- [ ] **Step 1: 写失败测试**

创建 `src/features/settings/components/ProviderForm.test.tsx`：

```tsx
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";

vi.mock("framer-motion", () => {
  const createMotionComponent = (tag: string) => {
    const Component = (props: Record<string, unknown>) => {
      const { children, ...rest } = props;
      const { initial: _i, animate: _a, exit: _e, transition: _t, whileHover: _h, whileTap: _wt, layout: _l, layoutId: _li } = rest as Record<string, unknown>;
      return React.createElement(tag, rest, children as React.ReactNode);
    };
    Component.displayName = `motion.${tag}`;
    return Component;
  };
  return {
    motion: new Proxy({}, { get: (_t, tag: string) => createMotionComponent(tag) }),
    AnimatePresence: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
  };
});

import ProviderForm from "./ProviderForm";
import type { ProviderConfig, ProviderPayload } from "../types";

afterEach(() => cleanup());

const baseConfig = (over: Partial<ProviderConfig> = {}): ProviderConfig => ({
  id: "cfg-1",
  name: "deepseek",
  api_mode: "openai-compat",
  api_host: "https://api.deepseek.com",
  api_path: "/v1/chat/completions",
  model_id: "deepseek-chat",
  display_name: "DeepSeek",
  context_window: 65536,
  max_output_tokens: 8192,
  purpose: "chat",
  embedding_dimension: null,
  is_active: false,
  created_at: "2026-06-24T00:00:00+00:00",
  updated_at: "2026-06-24T00:00:00+00:00",
  ...over,
});

describe("ProviderForm", () => {
  it("chat purpose 不渲染 embedding_dimension 字段", () => {
    render(<ProviderForm purpose="chat" onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.queryByLabelText(/向量维度/)).toBeNull();
  });

  it("embedding purpose 渲染 embedding_dimension 字段", () => {
    render(<ProviderForm purpose="embedding" onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByLabelText(/向量维度/)).toBeDefined();
  });

  it("编辑模式预填已有字段（api_key 留空待重输）", () => {
    render(<ProviderForm purpose="chat" initial={baseConfig()} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect((screen.getByLabelText(/展示名称/) as HTMLInputElement).value).toBe("DeepSeek");
    expect((screen.getByLabelText(/API 密钥/) as HTMLInputElement).value).toBe("");
  });

  it("提交时调用 onSubmit 并带上必填字段", () => {
    const onSubmit = vi.fn();
    render(<ProviderForm purpose="chat" onSubmit={onSubmit} onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/内部标识/), { target: { value: "my-cfg" } });
    fireEvent.change(screen.getByLabelText(/展示名称/), { target: { value: "My" } });
    fireEvent.change(screen.getByLabelText(/API 主机/), { target: { value: "https://x.com" } });
    fireEvent.change(screen.getByLabelText(/API 密钥/), { target: { value: "sk-1" } });
    fireEvent.change(screen.getByLabelText(/模型 ID/), { target: { value: "m1" } });
    fireEvent.click(screen.getByRole("button", { name: /保存/ }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    const payload = onSubmit.mock.calls[0][0] as ProviderPayload;
    expect(payload.name).toBe("my-cfg");
    expect(payload.api_key).toBe("sk-1");
    expect(payload.purpose).toBe("chat");
  });

  it("取消按钮调用 onClose", () => {
    const onClose = vi.fn();
    render(<ProviderForm purpose="chat" onSubmit={vi.fn()} onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: /取消/ }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `npx vitest run src/features/settings/components/ProviderForm.test.tsx`
Expected: FAIL — `Cannot find module './ProviderForm'`

- [ ] **Step 3: 实现 ProviderForm**

创建 `src/features/settings/components/ProviderForm.tsx`：

```tsx
import { useState, FormEvent } from "react";
import { motion } from "framer-motion";
import type { ProviderConfig, ProviderPayload, Purpose } from "../types";

interface ProviderFormProps {
  purpose: Purpose;
  initial?: ProviderConfig;
  onSubmit: (payload: ProviderPayload) => void;
  onClose: () => void;
}

const EMPTY: Omit<ProviderPayload, "purpose"> = {
  name: "",
  api_mode: "openai-compat",
  api_key: "",
  api_host: "",
  model_id: "",
  display_name: "",
  context_window: 65536,
  max_output_tokens: 8192,
};

export default function ProviderForm({ purpose, initial, onSubmit, onClose }: ProviderFormProps) {
  const [form, setForm] = useState<Omit<ProviderPayload, "purpose">>(() =>
    initial
      ? {
          name: initial.name,
          api_mode: initial.api_mode,
          api_key: "",
          api_host: initial.api_host,
          model_id: initial.model_id,
          display_name: initial.display_name,
          context_window: initial.context_window,
          max_output_tokens: initial.max_output_tokens,
          ...(purpose === "embedding" && initial.embedding_dimension
            ? { embedding_dimension: initial.embedding_dimension }
            : {}),
        }
      : { ...EMPTY },
  );

  const set = (key: keyof typeof form, value: string | number) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const payload: ProviderPayload = { ...form, purpose };
    onSubmit(payload);
  };

  const isEmbedding = purpose === "embedding";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
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
            <Field label="向量维度" type="number" value={String(form.embedding_dimension ?? "")} onChange={(v) => set("embedding_dimension", Number(v))} required />
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `npx vitest run src/features/settings/components/ProviderForm.test.tsx`
Expected: PASS（5 个用例）

- [ ] **Step 5: 类型检查 + 提交**

Run: `npx tsc --noEmit`

```bash
git add src/features/settings/components/ProviderForm.tsx src/features/settings/components/ProviderForm.test.tsx
git commit -m "feat(settings): 新增 ProviderForm 表单（chat/embedding 字段差异）"
```

---

## Task 3: ProviderList（配置列表）

**Files:**
- Create: `src/features/settings/components/ProviderList.tsx`
- Create: `src/features/settings/components/ProviderList.test.tsx`

- [ ] **Step 1: 写失败测试**

创建 `src/features/settings/components/ProviderList.test.tsx`：

```tsx
import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";

vi.mock("framer-motion", () => {
  const createMotionComponent = (tag: string) => {
    const Component = (props: Record<string, unknown>) => {
      const { children, ...rest } = props;
      return React.createElement(tag, rest, children as React.ReactNode);
    };
    Component.displayName = `motion.${tag}`;
    return Component;
  };
  return {
    motion: new Proxy({}, { get: (_t, tag: string) => createMotionComponent(tag) }),
    AnimatePresence: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
  };
});

import ProviderList from "./ProviderList";
import type { ProviderConfig } from "../types";

afterEach(() => cleanup());

const makeConfig = (over: Partial<ProviderConfig> = {}): ProviderConfig => ({
  id: "cfg-1",
  name: "deepseek",
  api_mode: "openai-compat",
  api_host: "https://api.deepseek.com",
  api_path: "/v1/chat/completions",
  model_id: "deepseek-chat",
  display_name: "DeepSeek",
  context_window: 65536,
  max_output_tokens: 8192,
  purpose: "chat",
  embedding_dimension: null,
  is_active: false,
  created_at: "",
  updated_at: "",
  ...over,
});

describe("ProviderList", () => {
  it("渲染每条配置的展示名与模型 ID", () => {
    render(
      <ProviderList
        providers={[makeConfig({ display_name: "DeepSeek", model_id: "deepseek-chat" })]}
        onActivate={vi.fn()}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText("DeepSeek")).toBeDefined();
    expect(screen.getByText("deepseek-chat")).toBeDefined();
  });

  it("激活项显示已激活标记", () => {
    render(
      <ProviderList
        providers={[makeConfig({ is_active: true })]}
        onActivate={vi.fn()}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText(/已激活/)).toBeDefined();
  });

  it("点击设为激活调用 onActivate", () => {
    const onActivate = vi.fn();
    render(
      <ProviderList
        providers={[makeConfig()]}
        onActivate={onActivate}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /设为激活/ }));
    expect(onActivate).toHaveBeenCalledWith("cfg-1");
  });

  it("点击编辑调用 onEdit（传整条配置）", () => {
    const onEdit = vi.fn();
    const cfg = makeConfig();
    render(
      <ProviderList providers={[cfg]} onActivate={vi.fn()} onEdit={onEdit} onDelete={vi.fn()} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /编辑/ }));
    expect(onEdit).toHaveBeenCalledWith(cfg);
  });

  it("点击删除调用 onDelete", () => {
    const onDelete = vi.fn();
    render(
      <ProviderList
        providers={[makeConfig()]}
        onActivate={vi.fn()}
        onEdit={vi.fn()}
        onDelete={onDelete}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /删除/ }));
    expect(onDelete).toHaveBeenCalledWith("cfg-1");
  });

  it("空列表显示占位提示", () => {
    render(
      <ProviderList providers={[]} onActivate={vi.fn()} onEdit={vi.fn()} onDelete={vi.fn()} />,
    );
    expect(screen.getByText(/暂无配置/)).toBeDefined();
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `npx vitest run src/features/settings/components/ProviderList.test.tsx`
Expected: FAIL — `Cannot find module './ProviderList'`

- [ ] **Step 3: 实现 ProviderList**

创建 `src/features/settings/components/ProviderList.tsx`：

```tsx
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `npx vitest run src/features/settings/components/ProviderList.test.tsx`
Expected: PASS（6 个用例）

- [ ] **Step 5: 类型检查 + 提交**

Run: `npx tsc --noEmit`

```bash
git add src/features/settings/components/ProviderList.tsx src/features/settings/components/ProviderList.test.tsx
git commit -m "feat(settings): 新增 ProviderList 列表（激活态与行内操作）"
```

---

## Task 4: PurposeSection（chat/embedding 分区）

**Files:**
- Create: `src/features/settings/components/PurposeSection.tsx`
- Create: `src/features/settings/components/PurposeSection.test.tsx`

- [ ] **Step 1: 写失败测试**

创建 `src/features/settings/components/PurposeSection.test.tsx`：

```tsx
import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";

vi.mock("framer-motion", () => {
  const createMotionComponent = (tag: string) => {
    const Component = (props: Record<string, unknown>) => {
      const { children, ...rest } = props;
      return React.createElement(tag, rest, children as React.ReactNode);
    };
    Component.displayName = `motion.${tag}`;
    return Component;
  };
  return {
    motion: new Proxy({}, { get: (_t, tag: string) => createMotionComponent(tag) }),
    AnimatePresence: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
  };
});

import PurposeSection from "./PurposeSection";

afterEach(() => cleanup());

describe("PurposeSection", () => {
  it("chat 分区显示「聊天模型」标题且不显示重建提示", () => {
    render(
      <PurposeSection purpose="chat" providers={[]} onAdd={vi.fn()} onActivate={vi.fn()} onEdit={vi.fn()} onDelete={vi.fn()} />,
    );
    expect(screen.getByText(/聊天模型/)).toBeDefined();
    expect(screen.queryByText(/重建/)).toBeNull();
  });

  it("embedding 分区显示「向量模型」标题与重建提示", () => {
    render(
      <PurposeSection purpose="embedding" providers={[]} onAdd={vi.fn()} onActivate={vi.fn()} onEdit={vi.fn()} onDelete={vi.fn()} />,
    );
    expect(screen.getByText(/向量模型/)).toBeDefined();
    expect(screen.getByText(/重建/)).toBeDefined();
  });

  it("点击新增按钮调用 onAdd", () => {
    const onAdd = vi.fn();
    render(
      <PurposeSection purpose="chat" providers={[]} onAdd={onAdd} onActivate={vi.fn()} onEdit={vi.fn()} onDelete={vi.fn()} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /新增/ }));
    expect(onAdd).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `npx vitest run src/features/settings/components/PurposeSection.test.tsx`
Expected: FAIL — `Cannot find module './PurposeSection'`

- [ ] **Step 3: 实现 PurposeSection**

创建 `src/features/settings/components/PurposeSection.tsx`：

```tsx
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `npx vitest run src/features/settings/components/PurposeSection.test.tsx`
Expected: PASS（3 个用例）

- [ ] **Step 5: 类型检查 + 提交**

Run: `npx tsc --noEmit`

```bash
git add src/features/settings/components/PurposeSection.tsx src/features/settings/components/PurposeSection.test.tsx
git commit -m "feat(settings): 新增 PurposeSection 分区容器（含 embedding 重建提示）"
```

---

## Task 5: SettingsPage（设置页主容器）

**Files:**
- Create: `src/features/settings/pages/SettingsPage.tsx`
- Create: `src/features/settings/pages/SettingsPage.test.tsx`

- [ ] **Step 1: 写失败测试**

创建 `src/features/settings/pages/SettingsPage.test.tsx`：

```tsx
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/react";

vi.mock("framer-motion", () => {
  const createMotionComponent = (tag: string) => {
    const Component = (props: Record<string, unknown>) => {
      const { children, ...rest } = props;
      return React.createElement(tag, rest, children as React.ReactNode);
    };
    Component.displayName = `motion.${tag}`;
    return Component;
  };
  return {
    motion: new Proxy({}, { get: (_t, tag: string) => createMotionComponent(tag) }),
    AnimatePresence: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
  };
});

vi.mock("../api/providerApi", () => ({
  listProviders: vi.fn(),
  createProvider: vi.fn(),
  updateProvider: vi.fn(),
  deleteProvider: vi.fn(),
  activateProvider: vi.fn(),
  getActiveProvider: vi.fn(),
}));

import {
  listProviders,
  createProvider,
  activateProvider,
  deleteProvider,
} from "../api/providerApi";
import SettingsPage from "./SettingsPage";
import type { ProviderConfig } from "../types";

afterEach(() => cleanup());

const chatConfig = (over: Partial<ProviderConfig> = {}): ProviderConfig => ({
  id: "chat-1",
  name: "deepseek",
  api_mode: "openai-compat",
  api_host: "https://api.deepseek.com",
  api_path: "/v1/chat/completions",
  model_id: "deepseek-chat",
  display_name: "DeepSeek",
  context_window: 65536,
  max_output_tokens: 8192,
  purpose: "chat",
  embedding_dimension: null,
  is_active: true,
  created_at: "",
  updated_at: "",
  ...over,
});

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (listProviders as ReturnType<typeof vi.fn>).mockImplementation(async (purpose?: string) => {
      if (purpose === "chat") return [chatConfig()];
      return [];
    });
  });

  it("挂载时并行加载 chat 与 embedding 列表", async () => {
    render(<SettingsPage onBack={vi.fn()} />);
    await waitFor(() => {
      expect(listProviders).toHaveBeenCalledWith("chat");
      expect(listProviders).toHaveBeenCalledWith("embedding");
    });
    expect(await screen.findByText("DeepSeek")).toBeDefined();
  });

  it("返回按钮调用 onBack", async () => {
    const onBack = vi.fn();
    render(<SettingsPage onBack={onBack} />);
    fireEvent.click(screen.getByRole("button", { name: /返回工作区/ }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("点击新增打开表单，提交后调用 createProvider 并刷新", async () => {
    (createProvider as ReturnType<typeof vi.fn>).mockResolvedValue(chatConfig({ id: "new" }));
    render(<SettingsPage onBack={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("DeepSeek")).toBeDefined());

    fireEvent.click(screen.getAllByRole("button", { name: /新增/ })[0]);
    expect(screen.getByRole("heading", { name: /新增配置/ })).toBeDefined();
  });

  it("点击设为激活调用 activateProvider 并刷新该分区", async () => {
    (activateProvider as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "chat-1" });
    (listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([chatConfig({ is_active: false })]);
    render(<SettingsPage onBack={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("设为激活")).toBeDefined());

    fireEvent.click(screen.getByText("设为激活"));
    await waitFor(() => expect(activateProvider).toHaveBeenCalledWith("chat-1"));
  });

  it("点击删除调用 deleteProvider", async () => {
    (deleteProvider as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    (listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([chatConfig({ is_active: false })]);
    render(<SettingsPage onBack={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("删除")).toBeDefined());

    fireEvent.click(screen.getByText("删除"));
    await waitFor(() => expect(deleteProvider).toHaveBeenCalledWith("chat-1"));
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `npx vitest run src/features/settings/pages/SettingsPage.test.tsx`
Expected: FAIL — `Cannot find module './SettingsPage'`

- [ ] **Step 3: 实现 SettingsPage**

创建 `src/features/settings/pages/SettingsPage.tsx`：

```tsx
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `npx vitest run src/features/settings/pages/SettingsPage.test.tsx`
Expected: PASS（5 个用例）

- [ ] **Step 5: 类型检查 + 提交**

Run: `npx tsc --noEmit`

```bash
git add src/features/settings/pages/SettingsPage.tsx src/features/settings/pages/SettingsPage.test.tsx
git commit -m "feat(settings): 新增 SettingsPage 设置页（串联分区与表单，CRUD 联动刷新）"
```

---

## Task 6: App 视图切换 + 齿轮入口

**Files:**
- Modify: `src/features/workspace/type.ts:116-124`
- Modify: `src/features/workspace/pages/WorkspacePage.tsx:343-347`
- Modify: `src/App.tsx`
- Modify: `src/App.test.tsx`

- [ ] **Step 1: 写失败测试**

整体替换 `src/App.test.tsx`（在现有 framer-motion mock 基础上增加 providerApi mock，并补 settings 视图用例）：

```tsx
import React from "react";
import { describe, it, expect, vi, afterEach, beforeEach, afterAll } from "vitest";
import { render, screen, cleanup, act, fireEvent } from "@testing-library/react";
import App from "./App";

vi.mock("framer-motion", () => {
  const createMotionComponent = (tag: string) => {
    const Component = (props: Record<string, unknown>) => {
      const { children, ...rest } = props;
      const { initial: _i, animate: _a, exit: _e, transition: _t, whileInView: _w, whileHover: _h, whileTap: _wt, viewport: _v, variants: _vr, layout: _l, layoutId: _li } = rest as Record<string, unknown>;
      return React.createElement(tag, rest, children as React.ReactNode);
    };
    Component.displayName = `motion.${tag}`;
    return Component;
  };
  return {
    motion: new Proxy({}, { get: (_t, tag: string) => createMotionComponent(tag) }),
    AnimatePresence: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
  };
});

vi.mock("./features/settings/api/providerApi", () => ({
  listProviders: vi.fn().mockResolvedValue([]),
  createProvider: vi.fn(),
  updateProvider: vi.fn(),
  deleteProvider: vi.fn(),
  activateProvider: vi.fn(),
  getActiveProvider: vi.fn().mockResolvedValue({ id: "cfg-1" }),
}));

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("App", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterAll(() => {
    vi.useRealTimers();
  });

  it("renders splash screen initially", () => {
    render(<App />);
    act(() => { vi.advanceTimersByTime(2000); });
    expect(screen.getByText("GreenBean Study Assistant")).toBeDefined();
  });

  it("shows workspace after splash auto-dismiss", () => {
    render(<App />);
    act(() => { vi.advanceTimersByTime(3800); });
    expect(screen.getByText("我的文档")).toBeDefined();
  });

  it("点击齿轮切换到设置页，返回回到工作区", () => {
    render(<App />);
    act(() => { vi.advanceTimersByTime(3800); });
    expect(screen.getByText("我的文档")).toBeDefined();

    // 齿轮按钮（title="设置"）
    const settingsBtn = screen.getByTitle("设置");
    fireEvent.click(settingsBtn);
    expect(screen.getByText("模型设置")).toBeDefined();

    // 返回工作区
    fireEvent.click(screen.getByRole("button", { name: /返回工作区/ }));
    expect(screen.getByText("我的文档")).toBeDefined();
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `npx vitest run src/App.test.tsx`
Expected: FAIL — 点击齿轮后无法切换到设置页，`模型设置` 文本找不到（App 尚未实现 settings 视图；齿轮按钮本身已存在）

- [ ] **Step 3: 改 WorkspacePageProps + 齿轮 + App 视图**

修改 `src/features/workspace/type.ts`，给 `WorkspacePageProps` 追加可选回调：

```typescript
export interface WorkspacePageProps {
  /** 工作区唯一标识（可选，后续可根据此加载不同数据） */
  workspaceId?: string;
  initialFiles?: FileItem[];
  initialFolders?: Folder[];
  initialSections?: SectionNode[];
  initialContentBlocks?: ContentBlock[];
  initialFootnotes?: FootnoteReference[];
  /** 打开模型设置页（由 App 层注入）。 */
  onOpenSettings?: () => void;
}
```

修改 `src/features/workspace/pages/WorkspacePage.tsx`：
1. 在函数签名解构 `onOpenSettings`：

```typescript
function WorkspacePage({ workspaceId, initialFiles = [], initialFolders = DEFAULT_FOLDERS, initialSections = [], initialContentBlocks = [], initialFootnotes = [], onOpenSettings }: WorkspacePageProps) {
```

2. 将齿轮按钮（原 line 343-347，`title="设置"` 的 `<button>`）加 `onClick`：

```tsx
            <button onClick={onOpenSettings} className="cursor-pointer w-9 h-9 rounded-lg flex items-center justify-center text-neutral-400 hover:bg-black/10 transition-all" title="设置">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </button>
```

整体替换 `src/App.tsx`：

```tsx
import { useState, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import SplashScreen from "./features/home/components/SplashScreen";
import WorkspacePage from "./features/workspace/pages/WorkspacePage";
import SettingsPage from "./features/settings/pages/SettingsPage";

type View = "splash" | "workspace" | "settings";

function App() {
  const [view, setView] = useState<View>("splash");

  const handleSplashDone = useCallback(() => setView("workspace"), []);
  const openSettings = useCallback(() => setView("settings"), []);
  const backToWorkspace = useCallback(() => setView("workspace"), []);

  return (
    <div>
      <AnimatePresence mode="wait">
        {view === "splash" && (
          <SplashScreen key="splash" onSkip={handleSplashDone} />
        )}
        {view === "workspace" && (
          <WorkspacePage key="workspace" onOpenSettings={openSettings} />
        )}
        {view === "settings" && (
          <SettingsPage key="settings" onBack={backToWorkspace} />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
```

- [ ] **Step 4: 运行测试验证通过**

Run: `npx vitest run src/App.test.tsx`
Expected: PASS（3 个用例）

- [ ] **Step 5: 类型检查 + 提交**

Run: `npx tsc --noEmit`

```bash
git add src/features/workspace/type.ts src/features/workspace/pages/WorkspacePage.tsx src/App.tsx src/App.test.tsx
git commit -m "feat(settings): App 扩展 splash/workspace/settings 三态视图与齿轮入口"
```

---

## Task 7: 首启缺配置引导

**Files:**
- Modify: `src/App.tsx`
- Modify: `src/App.test.tsx`

- [ ] **Step 1: 写失败测试**

Task 7 把 splash 的 `onSkip` 改为异步（内部 `getActiveProvider` 探测），因此需先对 Task 6 写入的 `App.test.tsx` 做三处前置调整：

**a)** 顶部 import 区追加（拿到被 mock 的 `getActiveProvider` 以便每个用例前重置，注意须在 `vi.mock(...)` 之后）：

```tsx
import { getActiveProvider } from "./features/settings/api/providerApi";
```

**b)** 将 Task 6 中 `shows workspace after splash auto-dismiss` 用例的同步 act 改为异步（因 onSkip 现为 async）：

```tsx
  it("shows workspace after splash auto-dismiss", async () => {
    render(<App />);
    await act(async () => { vi.advanceTimersByTime(3800); });
    expect(screen.getByText("我的文档")).toBeDefined();
  });
```

**c)** 在 `describe("App", ...)` 的 `beforeEach` 内重置 `getActiveProvider` 默认为「两者均已配置」，避免用例间 once 状态残留：

```tsx
  beforeEach(() => {
    vi.useFakeTimers();
    (getActiveProvider as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "cfg-1" });
  });
```

然后在 `describe` 内追加以下用例（用 `mockRejectedValueOnce` 模拟缺失）：

```tsx
  it("两者均已配置时不弹引导，直接进入工作区", async () => {
    render(<App />);
    await act(async () => { vi.advanceTimersByTime(3800); });
    expect(await screen.findByText("我的文档")).toBeDefined();
    expect(screen.queryByText(/尚未配置/)).toBeNull();
  });

  it("缺 chat 配置时弹引导，确认后进入设置页", async () => {
    (getActiveProvider as ReturnType<typeof vi.fn>)
      .mockRejectedValueOnce(new Error("404"))
      .mockResolvedValueOnce({ id: "embed-1" });

    render(<App />);
    await act(async () => { vi.advanceTimersByTime(3800); });

    expect(await screen.findByText(/尚未配置/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: /前往设置/ }));
    expect(screen.getByText("模型设置")).toBeDefined();
  });

  it("引导可关闭，暂不配置进入工作区", async () => {
    (getActiveProvider as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ id: "chat-1" })
      .mockRejectedValueOnce(new Error("404"));

    render(<App />);
    await act(async () => { vi.advanceTimersByTime(3800); });

    expect(await screen.findByText(/尚未配置/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: /稍后再说/ }));
    expect(screen.getByText("我的文档")).toBeDefined();
  });
```

- [ ] **Step 2: 运行测试验证失败**

Run: `npx vitest run src/App.test.tsx`
Expected: FAIL — `尚未配置` 找不到（引导 Modal 未实现）

- [ ] **Step 3: 改 App.tsx 加首启引导**

修改 `src/App.tsx`（在 Task 6 基础上）：在顶部 import 增加 `useEffect`、`getActiveProvider`，并扩展组件：

```tsx
import { useState, useCallback, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import SplashScreen from "./features/home/components/SplashScreen";
import WorkspacePage from "./features/workspace/pages/WorkspacePage";
import SettingsPage from "./features/settings/pages/SettingsPage";
import { getActiveProvider } from "./features/settings/api/providerApi";

type View = "splash" | "workspace" | "settings";

function App() {
  const [view, setView] = useState<View>("splash");
  const [showGuide, setShowGuide] = useState(false);

  const openSettings = useCallback(() => {
    setShowGuide(false);
    setView("settings");
  }, []);
  const backToWorkspace = useCallback(() => setView("workspace"), []);

  const handleSplashDone = useCallback(() => {
    void Promise.allSettled([
      getActiveProvider("chat"),
      getActiveProvider("embedding"),
    ]).then((results) => {
      const missing = results.some((r) => r.status === "rejected");
      if (missing) {
        setShowGuide(true);
      } else {
        setView("workspace");
      }
    });
  }, []);

  // splash 自身有 auto-dismiss（3.8s）调 onSkip；这里兼容 splash 未自动跳但引导已就绪的情况
  useEffect(() => {
    if (view === "settings") setShowGuide(false);
  }, [view]);

  return (
    <div>
      <AnimatePresence mode="wait">
        {view === "splash" && (
          <SplashScreen key="splash" onSkip={handleSplashDone} />
        )}
        {view === "workspace" && (
          <WorkspacePage key="workspace" onOpenSettings={openSettings} />
        )}
        {view === "settings" && (
          <SettingsPage key="settings" onBack={backToWorkspace} />
        )}
      </AnimatePresence>

      {showGuide && view !== "settings" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 text-center shadow-xl">
            <p className="mb-4 text-sm text-neutral-700">
              尚未配置 聊天 / 向量 模型，是否前往设置？
            </p>
            <div className="flex justify-center gap-2">
              <button
                onClick={() => {
                  setShowGuide(false);
                  setView("workspace");
                }}
                className="rounded-lg px-4 py-2 text-sm text-neutral-500 hover:bg-black/5"
              >
                稍后再说
              </button>
              <button
                onClick={openSettings}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700"
              >
                前往设置
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
```

> 注：splash 组件在 3.8s 后调用 `onSkip`，这里把 `onSkip` 接到 `handleSplashDone`，由它做配置探测并决定进入 workspace 还是弹引导。原 splash 的自动消失行为不变。

- [ ] **Step 4: 运行测试验证通过**

Run: `npx vitest run src/App.test.tsx`
Expected: PASS（6 个用例：3 个 Task 6 + 3 个 Task 7）

- [ ] **Step 5: 类型检查 + 全量前端验证 + 提交**

Run: `npx tsc --noEmit`
Run: `npm run test:frontend`
Expected: 全部 PASS

```bash
git add src/App.tsx src/App.test.tsx
git commit -m "feat(settings): 首启缺 chat/embedding 配置时弹引导 Modal"
```

---

## Self-Review

**Spec 覆盖核对：**
- 5.5.1 视图切换（splash/workspace/settings 三态）→ Task 6 ✓
- 5.5.2 `src/features/settings/` 结构（types/providerApi/SettingsPage/PurposeSection/ProviderList/ProviderForm）→ Task 1-5 ✓
- 5.5.3 设置页 UI（chat/embedding 分区、激活单选、表单字段、embedding 重建提示、列表不展示 api_key）→ Task 2-5 ✓（列表只渲染 display_name/model_id/is_active，不含 api_key；表单 password 输入）
- 5.5.4 首启引导（并行探测、缺失弹 Modal、可跳设置/可关闭）→ Task 7 ✓
- 5.6 通信（复用 apiClient / vite proxy）→ Task 1（providerApi 复用 request）✓
- 7.2 前端测试（providerApi.test、组件 test、首启分支、App 视图切换）→ Task 1-7 ✓
- 9 验收 1/6（前端设置页 CRUD + 激活隔离、首启引导跳转）→ Task 5/7 ✓

**类型一致性核对：** `Purpose = "chat" | "embedding"`、`ProviderConfig`（含 embedding_dimension: number|null）、`ProviderPayload.api_key: string`、`ActivateResponse`、`listProviders(purpose?)`、`createProvider(payload)`、`updateProvider(id, Partial)`、`activateProvider(id)`、`getActiveProvider(purpose)`、`WorkspacePageProps.onOpenSettings?`、`SettingsPageProps.onBack`、`View = "splash"|"workspace"|"settings"` 跨任务命名一致 ✓

**已知执行注意：**
- 组件测试统一 mock framer-motion（计划已给出工厂），避免动画副作用。
- `App.test.tsx` 整体替换在 Task 6，Task 7 在其 `describe` 内追加用例（不重写 framer-motion/providerApi mock）。
- 后端 Response 已脱敏 `api_key`，前端 `ProviderConfig` 类型不含 `api_key`；编辑时 `ProviderForm` 的 api_key 留空待重输（符合 spec 5.5.3）。
- 首启引导用 `Promise.allSettled` 探测，任一 rejected（后端 404「没有已激活的 provider」）即视为缺失。

---

## Execution Handoff

前端计划完成，保存于 `docs/superpowers/plans/2026-06-24-api-config-frontend.md`。两种执行方式：

**1. Subagent-Driven（推荐）** — 每个 Task 派独立 subagent，任务间审查，迭代快。
**2. Inline Execution** — 当前会话按 executing-plans 批量执行，带检查点。

主人选哪种？

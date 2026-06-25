import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
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

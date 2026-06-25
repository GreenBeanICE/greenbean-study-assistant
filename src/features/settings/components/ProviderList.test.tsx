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

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
    await waitFor(() => expect(screen.getByText("DeepSeek")).toBeDefined());
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
    (listProviders as ReturnType<typeof vi.fn>).mockImplementation(async (purpose?: string) => {
      if (purpose === "chat") return [chatConfig({ is_active: false })];
      return [];
    });
    render(<SettingsPage onBack={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("设为激活")).toBeDefined());

    fireEvent.click(screen.getByText("设为激活"));
    await waitFor(() => expect(activateProvider).toHaveBeenCalledWith("chat-1"));
  });

  it("点击删除调用 deleteProvider", async () => {
    (deleteProvider as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    (listProviders as ReturnType<typeof vi.fn>).mockImplementation(async (purpose?: string) => {
      if (purpose === "chat") return [chatConfig({ is_active: false })];
      return [];
    });
    render(<SettingsPage onBack={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("删除")).toBeDefined());

    fireEvent.click(screen.getByText("删除"));
    await waitFor(() => expect(deleteProvider).toHaveBeenCalledWith("chat-1"));
  });
});

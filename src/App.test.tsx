import React from "react";
import { describe, it, expect, vi, afterEach, beforeEach, afterAll } from "vitest";
import { render, screen, cleanup, act, fireEvent } from "@testing-library/react";
import App from "./App";
import { getActiveProvider } from "./features/settings/api/providerApi";

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
    (getActiveProvider as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "cfg-1" });
  });

  afterAll(() => {
    vi.useRealTimers();
  });

  it("renders splash screen initially", () => {
    render(<App />);
    act(() => { vi.advanceTimersByTime(2000); });
    expect(screen.getByText("GreenBean Study Assistant")).toBeDefined();
  });

  it("shows workspace after splash auto-dismiss", async () => {
    render(<App />);
    await act(async () => { vi.advanceTimersByTime(3800); await vi.runAllTicks(); });
    expect(screen.getByText("我的文档")).toBeDefined();
  });

  it("点击齿轮切换到设置页，返回回到工作区", async () => {
    render(<App />);
    await act(async () => { vi.advanceTimersByTime(3800); await vi.runAllTicks(); });
    expect(screen.getByText("我的文档")).toBeDefined();

    const settingsBtn = screen.getByTitle("设置");
    await act(async () => {
      fireEvent.click(settingsBtn);
      await vi.runAllTicks();
    });
    expect(screen.getByText("模型设置")).toBeDefined();

    fireEvent.click(screen.getByRole("button", { name: /返回工作区/ }));
    expect(screen.getByText("我的文档")).toBeDefined();
  });

  it("两者均已配置时不弹引导，直接进入工作区", async () => {
    render(<App />);
    await act(async () => { vi.advanceTimersByTime(3800); await vi.runAllTicks(); });
    expect(screen.getByText("我的文档")).toBeDefined();
    expect(screen.queryByText(/尚未配置/)).toBeNull();
  });

  it("缺 chat 配置时弹引导，确认后进入设置页", async () => {
    (getActiveProvider as ReturnType<typeof vi.fn>)
      .mockRejectedValueOnce(new Error("404"))
      .mockResolvedValueOnce({ id: "embed-1" });

    render(<App />);
    await act(async () => { vi.advanceTimersByTime(3800); await vi.runAllTicks(); });

    expect(screen.getByText(/尚未配置/)).toBeDefined();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /前往设置/ }));
      await vi.runAllTicks();
    });
    expect(screen.getByText("模型设置")).toBeDefined();
  });

  it("缺配置时退出欢迎页并显示工作区引导", async () => {
    (getActiveProvider as ReturnType<typeof vi.fn>)
      .mockRejectedValueOnce(new Error("404"))
      .mockResolvedValueOnce({ id: "embed-1" });

    render(<App />);
    await act(async () => {
      vi.advanceTimersByTime(3800);
      await vi.runAllTicks();
    });

    expect(screen.queryByText("GreenBean Study Assistant")).toBeNull();
    expect(screen.getByText("我的文档")).toBeDefined();
    expect(screen.getByText(/尚未配置/)).toBeDefined();
  });

  it("引导可关闭，暂不配置进入工作区", async () => {
    (getActiveProvider as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ id: "chat-1" })
      .mockRejectedValueOnce(new Error("404"));

    render(<App />);
    await act(async () => { vi.advanceTimersByTime(3800); await vi.runAllTicks(); });

    expect(screen.getByText(/尚未配置/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: /稍后再说/ }));
    expect(screen.getByText("我的文档")).toBeDefined();
  });
});

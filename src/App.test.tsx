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

    const settingsBtn = screen.getByTitle("设置");
    fireEvent.click(settingsBtn);
    expect(screen.getByText("模型设置")).toBeDefined();

    fireEvent.click(screen.getByRole("button", { name: /返回工作区/ }));
    expect(screen.getByText("我的文档")).toBeDefined();
  });
});

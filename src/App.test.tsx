import React from "react";
import { describe, it, expect, vi, afterEach, beforeEach, afterAll } from "vitest";
import { render, screen, cleanup, act } from "@testing-library/react";
import App from "./App";

vi.mock("framer-motion", () => {
  const createMotionComponent = (tag: string) => {
    const Component = (props: Record<string, unknown>) => {
      const { children, ...rest } = props;
      const {
        initial: _i, animate: _a, exit: _e, transition: _t,
        whileInView: _w, whileHover: _h, whileTap: _wt,
        viewport: _v, variants: _vr, layout: _l, layoutId: _li,
        ...cleanProps
      } = rest as Record<string, unknown>;
      return React.createElement(tag, cleanProps, children as React.ReactNode);
    };
    Component.displayName = `motion.${tag}`;
    return Component;
  };

  return {
    motion: new Proxy(
      {},
      { get: (_target, tag: string) => createMotionComponent(tag) },
    ),
    AnimatePresence: ({ children }: { children: React.ReactNode }) =>
      React.createElement(React.Fragment, null, children),
  };
});

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
    // Advance timers past the subtitle phase (1700ms for subtitle, 800ms + 600ms for welcome)
    act(() => { vi.advanceTimersByTime(2000); });
    expect(screen.getByText("GreenBean Study Assistant")).toBeDefined();
  });

  it("shows workspace after splash auto-dismiss", () => {
    render(<App />);
    act(() => { vi.advanceTimersByTime(3800); });
    expect(screen.getByText("我的文档")).toBeDefined();
    expect(screen.queryByText("GreenBean Study Assistant")).toBeNull();
  });
});

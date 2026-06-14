import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
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
});

describe("App", () => {
  it("renders splash screen initially", () => {
    render(<App />);
    expect(screen.getByText("GreenBean Study Assistant")).toBeDefined();
  });

  it("renders skip button on splash", () => {
    render(<App />);
    expect(screen.getByText("跳过")).toBeDefined();
  });

  it("shows workspace after skipping splash", () => {
    render(<App />);
    const skipBtn = screen.getByText("跳过");
    fireEvent.click(skipBtn);
    expect(screen.getByText("Workspace")).toBeDefined();
    expect(screen.queryByText("跳过")).toBeNull();
  });
});
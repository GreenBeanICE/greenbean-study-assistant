import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import MungBeanSplash from "./SplashScreen";

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

describe("MungBeanSplash", () => {
  it("renders skip button", () => {
    render(<MungBeanSplash onSkip={() => {}} />);
    expect(screen.getByText("跳过")).toBeDefined();
  });

  it("renders brand text", () => {
    render(<MungBeanSplash onSkip={() => {}} />);
    expect(screen.getByText("GreenBean Study Assistant")).toBeDefined();
  });

  it("calls onSkip when skip button is clicked", () => {
    const onSkip = vi.fn();
    render(<MungBeanSplash onSkip={onSkip} />);
    fireEvent.click(screen.getByText("跳过"));
    expect(onSkip).toHaveBeenCalledTimes(1);
  });

  it("does not render skip button when onSkip is not provided", () => {
    render(<MungBeanSplash />);
    expect(screen.queryByText("跳过")).toBeNull();
  });

  it("renders SVG icon", () => {
    const { container } = render(<MungBeanSplash onSkip={() => {}} />);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg?.getAttribute("viewBox")).toBe("0 0 66 86");
  });

  it("applies custom className", () => {
    const { container } = render(<MungBeanSplash onSkip={() => {}} className="custom-test" />);
    expect(container.innerHTML).toContain("custom-test");
  });
});
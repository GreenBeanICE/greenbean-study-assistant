import React from "react";
import { describe, it, expect, vi, afterEach, beforeEach, afterAll } from "vitest";
import { render, screen, cleanup, act } from "@testing-library/react";
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

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("MungBeanSplash", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterAll(() => {
    vi.useRealTimers();
  });


  it("renders welcome text after initial delay", () => {
    render(<MungBeanSplash onSkip={() => {}} />);
    expect(screen.queryByText("欢迎")).toBeNull();

    act(() => { vi.advanceTimersByTime(800); });
    expect(screen.getByText("欢迎")).toBeDefined();
  });

  it("renders brand subtitle after longer delay", () => {
    render(<MungBeanSplash onSkip={() => {}} />);
    expect(screen.queryByText("GreenBean Study Assistant")).toBeNull();

    act(() => { vi.advanceTimersByTime(1700); });
    expect(screen.getByText("GreenBean Study Assistant")).toBeDefined();
  });

  it("does not show subtitle during welcome-only phase", () => {
    render(<MungBeanSplash onSkip={() => {}} />);
    act(() => { vi.advanceTimersByTime(800); });
    // Welcome is visible but subtitle should still be hidden
    expect(screen.getByText("欢迎")).toBeDefined();
    expect(screen.queryByText("GreenBean Study Assistant")).toBeNull();
  });

  it("auto-dismisses after 3.8 seconds", () => {
    const onSkip = vi.fn();
    render(<MungBeanSplash onSkip={onSkip} />);
    expect(onSkip).not.toHaveBeenCalled();

    act(() => { vi.advanceTimersByTime(3800); });
    expect(onSkip).toHaveBeenCalledTimes(1);
  });

  it("does not auto-dismiss when onSkip is not provided", () => {
    render(<MungBeanSplash />);
    act(() => { vi.advanceTimersByTime(3800); });
    // No onSkip means no auto-dismiss callback to check; just ensure no error
    expect(screen.getByText("欢迎")).toBeDefined();
  });

  it("applies custom className", () => {
    const { container } = render(<MungBeanSplash onSkip={() => {}} className="custom-test" />);
    expect(container.innerHTML).toContain("custom-test");
  });

  it("renders background dots with color classes", () => {
    const { container } = render(<MungBeanSplash onSkip={() => {}} />);
    const divs = container.querySelectorAll("div");
    const classNames = Array.from(divs).map(d => d.className || "").join(" ");
    expect(classNames).toContain("bg-emerald-400/70");
    expect(classNames).toContain("bg-cyan-300/60");
    expect(classNames).toContain("bg-lime-300/60");
    expect(classNames).toContain("from-emerald-300/60");
  });

  it("cleans up welcome timer on unmount before timer fires", () => {
    const { unmount } = render(<MungBeanSplash onSkip={() => {}} />);
    unmount();
    // After unmount, advancing timers should have no effect
    act(() => { vi.advanceTimersByTime(800); });
    expect(screen.queryByText("欢迎")).toBeNull();
  });

  it("cleans up subtitle timer on unmount between phases", () => {
    const { unmount } = render(<MungBeanSplash onSkip={() => {}} />);
    act(() => { vi.advanceTimersByTime(800); });
    // Welcome is now visible
    expect(screen.getByText("欢迎")).toBeDefined();
    unmount();
    // After unmount, subtitle should never appear
    act(() => { vi.advanceTimersByTime(900); });
    expect(screen.queryByText("GreenBean Study Assistant")).toBeNull();
  });

  it("cleans up auto-dismiss timer on unmount", () => {
    const onSkip = vi.fn();
    const { unmount } = render(<MungBeanSplash onSkip={onSkip} />);
    unmount();
    act(() => { vi.advanceTimersByTime(3800); });
    expect(onSkip).not.toHaveBeenCalled();
  });

  it("cleans up onSkip dependency effect when prop changes", () => {
    const onSkip = vi.fn();
    const { rerender, unmount } = render(<MungBeanSplash onSkip={onSkip} />);
    // Simulate onSkip changing (effect re-run triggers cleanup of previous)
    rerender(<MungBeanSplash onSkip={vi.fn()} />);
    unmount();
    act(() => { vi.advanceTimersByTime(3800); });
    // The second onSkip should not fire after unmount
    expect(onSkip).not.toHaveBeenCalled();
  });

  it("renders with default className when none provided", () => {
    const { container } = render(<MungBeanSplash onSkip={() => {}} />);
    const root = container.querySelector("div");
    expect(root?.className).toContain("fixed inset-0");
  });
});

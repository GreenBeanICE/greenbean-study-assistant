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
    expect(screen.getByRole("heading", { name: /向量模型/ })).toBeDefined();
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

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import HomePage from "./HomePage";
import { createI18nWrapper } from "../../../test-utils";

// Mock framer-motion to avoid animation issues in tests
vi.mock("framer-motion", () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const createMotionComponent = (tag: string) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const Component = ({ children, ...props }: any) => {
      // Filter out framer-motion specific props to avoid React DOM warnings
      const {
        initial,
        animate,
        exit,
        transition,
        whileInView,
        whileHover,
        whileTap,
        viewport,
        variants,
        layout,
        layoutId,
        ...validProps
      } = props;
      return (React.createElement as (type: string, props: Record<string, unknown>, ...children: React.ReactNode[]) => React.ReactElement)(
        tag,
        validProps,
        children,
      );
    };
    Component.displayName = `motion.${tag}`;
    return Component;
  };

  return {
    motion: new Proxy(
      {},
      {
        get: (_target, tag: string) => createMotionComponent(tag),
      },
    ),
    AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

// Need React for createElement usage in mock
import React from "react";

describe("HomePage", () => {
  it("renders hero section in Chinese", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    expect(screen.getByText("让法国课程")).toBeDefined();
    expect(screen.getByText("不再难懂")).toBeDefined();
    expect(screen.getByText("开始使用")).toBeDefined();
    expect(screen.getByText("了解更多")).toBeDefined();
  });

  it("renders hero section in French", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("fr"),
    });
    expect(screen.getByText("Les cours français")).toBeDefined();
    expect(screen.getByText("enfin accessibles")).toBeDefined();
    expect(screen.getByText("Commencer")).toBeDefined();
    expect(screen.getByText("En savoir plus")).toBeDefined();
  });

  it("renders features section", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    expect(screen.getByText("课件智能解析")).toBeDefined();
    expect(screen.getByText("AI 深度分析")).toBeDefined();
    expect(screen.getByText("知识结构化")).toBeDefined();
    expect(screen.getByText("智能问答")).toBeDefined();
  });

  it("renders screenshots section with placeholders", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    expect(screen.getByText("课程概览")).toBeDefined();
    expect(screen.getByText("AI 问答")).toBeDefined();
    expect(screen.getByText("解析报告")).toBeDefined();
    expect(screen.getByText("文件管理")).toBeDefined();
    expect(screen.getByText("章节导航")).toBeDefined();
  });

  it("renders workflow section", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    expect(screen.getByText("三步搞定课程解析")).toBeDefined();
    expect(screen.getByText("上传文件")).toBeDefined();
    expect(screen.getByText("自动解析")).toBeDefined();
    expect(screen.getByText("深度互动")).toBeDefined();
  });

  it("renders bottom CTA section", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    expect(screen.getByText("准备好提升学习效率了吗？")).toBeDefined();
    expect(screen.getByText("免费开始使用")).toBeDefined();
  });

  it("renders upload zone", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    expect(screen.getByText("拖拽文件到此处，或点击上传")).toBeDefined();
  });

  it("renders footer", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    expect(screen.getByText("关于我们")).toBeDefined();
    expect(screen.getByText("隐私政策")).toBeDefined();
    expect(screen.getByText("使用条款")).toBeDefined();
  });

  it("renders footer in French", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("fr"),
    });
    expect(screen.getByText("À propos")).toBeDefined();
    expect(screen.getByText("Confidentialité")).toBeDefined();
    expect(screen.getByText("Conditions")).toBeDefined();
  });
});
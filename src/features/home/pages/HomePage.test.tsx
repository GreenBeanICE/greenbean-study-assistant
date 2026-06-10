import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import HomePage from "./HomePage";
import { createI18nWrapper } from "../../../test-utils";

// Mock framer-motion
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
    AnimatePresence: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
  };
});

describe("HomePage", () => {
  beforeEach(() => {
    // Mock scrollIntoView for all tests
    Element.prototype.scrollIntoView = vi.fn();
    // Mock scrollBy for all tests
    Element.prototype.scrollBy = vi.fn();
  });

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
    const fileMgmtElements = screen.getAllByText("文件管理");
    expect(fileMgmtElements.length).toBeGreaterThanOrEqual(1);
    const sectionNavElements = screen.getAllByText("章节导航");
    expect(sectionNavElements.length).toBeGreaterThanOrEqual(1);
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

  it("calls onLogin when upload zone is clicked", () => {
    const onLogin = vi.fn();
    render(<HomePage onLogin={onLogin} />, {
      wrapper: createI18nWrapper("zh"),
    });
    fireEvent.click(screen.getByText("拖拽文件到此处，或点击上传"));
    expect(onLogin).toHaveBeenCalled();
  });

  it("renders hero badge in Chinese", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    expect(screen.getByText("面向在法中国留学生")).toBeDefined();
  });

  it("calls scrollIntoView when '开始使用' is clicked", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    const startButton = screen.getByText("开始使用");
    fireEvent.click(startButton);
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled();
  });

  it("calls scrollIntoView when bottom CTA is clicked", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    fireEvent.click(screen.getByText("免费开始使用"));
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled();
  });

  it("calls scrollBy when left scroll button is clicked", () => {
    render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    const buttons = screen.getAllByRole("button");
    // Find buttons that are scroll buttons - they're children of divs with "absolute left-0"
    const { container } = render(<HomePage onLogin={() => {}} />, {
      wrapper: createI18nWrapper("zh"),
    });
    // Try clicking each button to exercise scroll
    const allButtons = screen.getAllByRole("button");
    for (const btn of allButtons) {
      fireEvent.click(btn);
    }
    // scrollBy should have been called from the scroll function
    expect(Element.prototype.scrollBy).toHaveBeenCalled();
  });
});
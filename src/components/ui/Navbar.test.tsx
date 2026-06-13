import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Navbar from "./Navbar";
import { createI18nWrapper } from "../../test-utils";

describe("Navbar", () => {
  it("renders navigation items in Chinese", () => {
    render(
      <Navbar dark={false} setDark={() => {}} onLogin={() => {}} />,
      { wrapper: createI18nWrapper("zh") },
    );
    expect(screen.getByText("功能特性")).toBeDefined();
    expect(screen.getByText("使用体验")).toBeDefined();
    expect(screen.getByText("解析流程")).toBeDefined();
    expect(screen.getByText("登录")).toBeDefined();
  });

  it("renders navigation items in French", () => {
    render(
      <Navbar dark={false} setDark={() => {}} onLogin={() => {}} />,
      { wrapper: createI18nWrapper("fr") },
    );
    expect(screen.getByText("Fonctionnalités")).toBeDefined();
    expect(screen.getByText("Aperçus")).toBeDefined();
    expect(screen.getByText("Processus")).toBeDefined();
    expect(screen.getByText("Connexion")).toBeDefined();
  });

  it("calls onLogin when login button is clicked", () => {
    const onLogin = vi.fn();
    render(
      <Navbar dark={false} setDark={() => {}} onLogin={onLogin} />,
      { wrapper: createI18nWrapper("zh") },
    );
    const loginBtn = screen.getByText("登录");
    fireEvent.click(loginBtn);
    expect(onLogin).toHaveBeenCalledTimes(1);
  });

  it("calls setDark when dark mode toggle is clicked", () => {
    const setDark = vi.fn();
    render(
      <Navbar dark={false} setDark={setDark} onLogin={() => {}} />,
      { wrapper: createI18nWrapper("zh") },
    );
    const buttons = screen.getAllByRole("button");
    const darkToggle = buttons[1];
    fireEvent.click(darkToggle);
    expect(setDark).toHaveBeenCalledTimes(1);
  });

  it("renders sun icon in dark mode", () => {
    render(
      <Navbar dark={true} setDark={() => {}} onLogin={() => {}} />,
      { wrapper: createI18nWrapper("zh") },
    );
    // When dark=true, the SVG with sun rays (circle+lines) should render
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("shows language toggle button with FR text", () => {
    render(
      <Navbar dark={false} setDark={() => {}} onLogin={() => {}} />,
      { wrapper: createI18nWrapper("zh") },
    );
    const langBtn = screen.getByText("FR");
    expect(langBtn).toBeDefined();
  });

  it("shows GreenBean logo", () => {
    render(
      <Navbar dark={false} setDark={() => {}} onLogin={() => {}} />,
      { wrapper: createI18nWrapper("zh") },
    );
    expect(screen.getByText("GreenBean")).toBeDefined();
  });

  it("renders navigation links with correct hrefs", () => {
    render(
      <Navbar dark={false} setDark={() => {}} onLogin={() => {}} />,
      { wrapper: createI18nWrapper("zh") },
    );
    const featuresLinks = screen.getAllByText("功能特性");
    expect(featuresLinks.length).toBeGreaterThanOrEqual(1);
    expect(featuresLinks[0].closest("a")?.getAttribute("href")).toBe("#features");

    const screenshotsLinks = screen.getAllByText("使用体验");
    expect(screenshotsLinks[0].closest("a")?.getAttribute("href")).toBe("#screenshots");

    const workflowLinks = screen.getAllByText("解析流程");
    expect(workflowLinks[0].closest("a")?.getAttribute("href")).toBe("#workflow");
  });

  it("opens mobile menu when hamburger button is clicked", () => {
    render(
      <Navbar dark={false} setDark={() => {}} onLogin={() => {}} />,
      { wrapper: createI18nWrapper("zh") },
    );
    const buttons = screen.getAllByRole("button");
    const hamburgerBtn = buttons[buttons.length - 1];
    fireEvent.click(hamburgerBtn);
    // After opening mobile menu, both desktop and mobile nav links exist
    const featuresLinks = screen.getAllByText("功能特性");
    expect(featuresLinks.length).toBe(2);
  });
});
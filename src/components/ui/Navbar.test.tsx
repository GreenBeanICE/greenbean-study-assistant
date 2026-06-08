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
    // Find the dark mode toggle button (contains SVG)
    const buttons = screen.getAllByRole("button");
    // The dark mode toggle is the second button (after language toggle)
    const darkToggle = buttons[1];
    fireEvent.click(darkToggle);
    expect(setDark).toHaveBeenCalledTimes(1);
  });

  it("toggles language button text", () => {
    render(
      <Navbar dark={false} setDark={() => {}} onLogin={() => {}} />,
      { wrapper: createI18nWrapper("zh") },
    );
    // Should show "FR" when lang is zh
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
    const featuresLink = screen.getByText("功能特性").closest("a");
    expect(featuresLink?.getAttribute("href")).toBe("#features");

    const screenshotsLink = screen.getByText("使用体验").closest("a");
    expect(screenshotsLink?.getAttribute("href")).toBe("#screenshots");

    const workflowLink = screen.getByText("解析流程").closest("a");
    expect(workflowLink?.getAttribute("href")).toBe("#workflow");
  });
});
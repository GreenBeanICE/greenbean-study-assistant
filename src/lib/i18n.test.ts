import { describe, it, expect } from "vitest";
import { translations } from "./i18n";

describe("i18n translations", () => {
  it("should have the same keys for zh and fr", () => {
    const zhKeys = Object.keys(translations.zh).sort();
    const frKeys = Object.keys(translations.fr).sort();
    expect(zhKeys).toEqual(frKeys);
  });

  it("should not have empty translations in zh", () => {
    for (const [key, value] of Object.entries(translations.zh)) {
      expect(value, `zh.${key} is empty`).toBeTruthy();
    }
  });

  it("should not have empty translations in fr", () => {
    for (const [key, value] of Object.entries(translations.fr)) {
      expect(value, `fr.${key} is empty`).toBeTruthy();
    }
  });

  it("should have all translation keys covered", () => {
    const zhKeys = Object.keys(translations.zh);
    const frKeys = Object.keys(translations.fr);
    expect(zhKeys.length).toBeGreaterThan(30);
    expect(frKeys.length).toBeGreaterThan(30);
  });

  it("should contain expected keys", () => {
    expect(translations.zh.heroTitle1).toBe("让法国课程");
    expect(translations.zh.loginTitle).toBe("登录以使用上传功能");
    expect(translations.zh.uploadPrompt).toBe("拖拽文件到此处，或点击上传");
    expect(translations.fr.heroTitle1).toBe("Les cours français");
    expect(translations.fr.loginTitle).toBe("Connectez-vous pour importer");
  });
});
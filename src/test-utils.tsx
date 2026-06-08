import type { ReactNode } from "react";
import { I18nContext, type Lang, translations } from "./lib/i18n";

/** 测试用的 Provider Wrapper，提供 i18n 上下文 */
export function createI18nWrapper(lang: Lang = "zh") {
  const t = (key: keyof typeof translations.zh) => translations[lang][key];
  const setLang = () => {};

  return function I18nWrapper({ children }: { children: ReactNode }) {
    return (
      <I18nContext.Provider value={{ lang, setLang, t }}>
        {children}
      </I18nContext.Provider>
    );
  };
}
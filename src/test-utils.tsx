import type { ReactNode } from "react";

/** 测试用的 Provider Wrapper */
export function createI18nWrapper(_lang?: string) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <>{children}</>;
  };
}
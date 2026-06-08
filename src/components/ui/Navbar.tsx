import { useState } from "react";
import { useI18n } from "../../lib/i18n";

interface NavbarProps {
  dark: boolean;
  setDark: React.Dispatch<React.SetStateAction<boolean>>;
  onLogin: () => void;
}

export default function Navbar({ dark, setDark, onLogin }: NavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { t, lang, setLang } = useI18n();

  const NAV_ITEMS = [
    { label: t("navFeatures"), href: "#features" },
    { label: t("navScreenshots"), href: "#screenshots" },
    { label: t("navWorkflow"), href: "#workflow" },
  ];

  return (
    <header className="fixed top-0 left-0 w-full h-14 z-50 backdrop-blur-xl bg-white/80 dark:bg-black/70 border-b border-black/5 dark:border-white/10">
      <div className="h-full max-w-7xl mx-auto px-4 md:px-8 flex items-center justify-between">
        {/* Logo */}
        <a href="#" className="text-base font-semibold tracking-tight select-none">
          GreenBean
        </a>

        {/* 桌面端导航 */}
        <nav className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="px-3 py-1.5 rounded-full text-sm text-neutral-600 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/10 transition"
            >
              {item.label}
            </a>
          ))}
        </nav>

        {/* 右侧操作区 */}
        <div className="flex items-center gap-1.5">
          {/* 语言切换 */}
          <button
            onClick={() => setLang(lang === "zh" ? "fr" : "zh")}
            className="px-2.5 py-1.5 rounded-full text-xs font-medium text-neutral-600 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/10 transition"
          >
            {lang === "zh" ? "FR" : "中文"}
          </button>

          {/* 夜间模式 */}
          <button
            onClick={() => setDark((prev) => !prev)}
            className="w-8 h-8 rounded-full flex items-center justify-center text-sm hover:bg-black/5 dark:hover:bg-white/10 transition"
          >
            {dark ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>

          {/* 登录按钮 */}
          <button
            onClick={onLogin}
            className="ml-1 px-4 py-1.5 rounded-full text-xs font-medium bg-black text-white dark:bg-white dark:text-black hover:opacity-85 transition"
          >
            {t("login")}
          </button>

          {/* 移动端汉堡菜单 */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden w-8 h-8 rounded-full flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/10 transition"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      {/* 移动端菜单 */}
      {mobileOpen && (
        <div className="md:hidden border-t border-black/5 dark:border-white/10 bg-white/95 dark:bg-black/80 backdrop-blur-xl">
          <div className="px-4 py-3 space-y-1">
            {NAV_ITEMS.map((item) => (
              <a
                key={item.label}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className="block px-3 py-2 rounded-xl text-sm text-neutral-600 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/10 transition"
              >
                {item.label}
              </a>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
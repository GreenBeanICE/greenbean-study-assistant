import { useState, useCallback } from "react";
import HomePage from "./features/home/pages/HomePage";
import WorkspacePage from "./features/workspace/pages/WorkspacePage";
import Navbar from "./components/ui/Navbar";
import LoginModal from "./features/home/components/LoginModal";
import { I18nContext, type Lang, translations } from "./lib/i18n";

type Page = "home" | "workspace";

function App() {
  const [dark, setDark] = useState(() => {
    if (typeof window !== "undefined") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return false;
  });

  const [lang, setLang] = useState<Lang>("zh");
  const [showLogin, setShowLogin] = useState(false);
  const [page, setPage] = useState<Page>("home");

  const openLogin = useCallback(() => setShowLogin(true), []);
  const closeLogin = useCallback(() => setShowLogin(false), []);
  const navigateToWorkspace = useCallback(() => setPage("workspace"), []);
  const navigateToHome = useCallback(() => setPage("home"), []);

  const t = useCallback(
    (key: keyof typeof translations.zh) => translations[lang][key],
    [lang],
  );

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      <div className={dark ? "dark" : ""}>
        {page === "home" && (
          <>
            <Navbar dark={dark} setDark={setDark} onLogin={openLogin} />
            <HomePage onLogin={openLogin} onStart={navigateToWorkspace} />
            <LoginModal open={showLogin} onClose={closeLogin} />
          </>
        )}
        {page === "workspace" && (
          <WorkspacePage dark={dark} setDark={setDark} lang={lang} setLang={setLang} onBack={navigateToHome} onLogout={navigateToHome} />
        )}
      </div>
    </I18nContext.Provider>
  );
}

export default App;
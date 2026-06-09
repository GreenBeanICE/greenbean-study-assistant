import { useState, useCallback } from "react";
import HomePage from "./features/home/pages/HomePage";
import Navbar from "./components/ui/Navbar";
import LoginModal from "./features/home/components/LoginModal";
import { I18nContext, type Lang, translations } from "./lib/i18n";

function App() {
  const [dark, setDark] = useState(() => {
    if (typeof window !== "undefined") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return false;
  });

  const [lang, setLang] = useState<Lang>("zh");
  const [showLogin, setShowLogin] = useState(false);

  const openLogin = useCallback(() => setShowLogin(true), []);
  const closeLogin = useCallback(() => setShowLogin(false), []);

  const t = useCallback(
    (key: keyof typeof translations.zh) => translations[lang][key],
    [lang],
  );

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      <div className={dark ? "dark" : ""}>
        <Navbar dark={dark} setDark={setDark} onLogin={openLogin} />
        <HomePage onLogin={openLogin} />
        <LoginModal open={showLogin} onClose={closeLogin} />
      </div>
    </I18nContext.Provider>
  );
}

export default App;
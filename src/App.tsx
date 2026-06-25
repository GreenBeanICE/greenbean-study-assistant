import { useState, useCallback, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import SplashScreen from "./features/home/components/SplashScreen";
import WorkspacePage from "./features/workspace/pages/WorkspacePage";
import SettingsPage from "./features/settings/pages/SettingsPage";
import { getActiveProvider } from "./features/settings/api/providerApi";

type View = "splash" | "workspace" | "settings";

function App() {
  const [view, setView] = useState<View>("splash");
  const [showGuide, setShowGuide] = useState(false);

  const openSettings = useCallback(() => {
    setShowGuide(false);
    setView("settings");
  }, []);
  const backToWorkspace = useCallback(() => setView("workspace"), []);

  const handleSplashDone = useCallback(() => {
    void Promise.allSettled([
      getActiveProvider("chat"),
      getActiveProvider("embedding"),
    ]).then((results) => {
      const missing = results.some((r) => r.status === "rejected");
      if (missing) {
        setShowGuide(true);
      } else {
        setView("workspace");
      }
    });
  }, []);

  useEffect(() => {
    if (view === "settings") setShowGuide(false);
  }, [view]);

  return (
    <div>
      <AnimatePresence mode="wait">
        {view === "splash" && (
          <SplashScreen key="splash" onSkip={handleSplashDone} />
        )}
        {view === "workspace" && (
          <WorkspacePage key="workspace" onOpenSettings={openSettings} />
        )}
        {view === "settings" && (
          <SettingsPage key="settings" onBack={backToWorkspace} />
        )}
      </AnimatePresence>

      {showGuide && view !== "settings" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 text-center shadow-xl">
            <p className="mb-4 text-sm text-neutral-700">
              尚未配置 聊天 / 向量 模型，是否前往设置？
            </p>
            <div className="flex justify-center gap-2">
              <button
                onClick={() => {
                  setShowGuide(false);
                  setView("workspace");
                }}
                className="rounded-lg px-4 py-2 text-sm text-neutral-500 hover:bg-black/5"
              >
                稍后再说
              </button>
              <button
                onClick={openSettings}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700"
              >
                前往设置
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

import { useState, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import SplashScreen from "./features/home/components/SplashScreen";
import WorkspacePage from "./features/workspace/pages/WorkspacePage";
import SettingsPage from "./features/settings/pages/SettingsPage";

type View = "splash" | "workspace" | "settings";

function App() {
  const [view, setView] = useState<View>("splash");

  const handleSplashDone = useCallback(() => setView("workspace"), []);
  const openSettings = useCallback(() => setView("settings"), []);
  const backToWorkspace = useCallback(() => setView("workspace"), []);

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
    </div>
  );
}

export default App;

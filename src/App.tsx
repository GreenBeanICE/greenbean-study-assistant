import { useState, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import SplashScreen from "./features/home/components/SplashScreen";
import WorkspacePage from "./features/workspace/pages/WorkspacePage";

function App() {
  const [showSplash, setShowSplash] = useState(true);

  const skipSplash = useCallback(() => setShowSplash(false), []);

  return (
    <div>
      <AnimatePresence mode="wait">
        {showSplash ? (
          <SplashScreen key="splash" onSkip={skipSplash} />
        ) : (
          <WorkspacePage key="workspace" />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
import { useState } from "react";
import SplashPage from "./features/home/pages/SplashPage";
import WorkspacePage from "./features/workspace/pages/WorkspacePage";

type Page = "splash" | "workspace";

function App() {
  const [page, setPage] = useState<Page>("splash");

  return (
    <div>
      {page === "splash" && (
        <SplashPage onStart={() => setPage("workspace")} />
      )}
      {page === "workspace" && (
        <WorkspacePage />
      )}
    </div>
  );
}

export default App;
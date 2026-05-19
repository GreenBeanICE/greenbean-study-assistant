import { useEffect, useState } from "react";
import HomePage from "./pages/HomePage";
import Navbar from "./components/ui/Navbar";

function App() {
  const [dark, setDark] = useState<boolean>(false);

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [dark]);

  return (
    <>
      <Navbar dark={dark} setDark={setDark} />

      <div className="min-h-screen bg-white text-black dark:bg-black dark:text-white transition-colors">
        <HomePage />
      </div>
    </>
  );
}

export default App;
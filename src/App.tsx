import { useEffect, useState } from "react";
import HomePage from "./pages/HomePage";
import Navbar from "./components/ui/Navbar";

function App() {
  // 深色模式状态
  const [dark, setDark] = useState(false);

  // 切换 dark class
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <div className="min-h-screen text-black dark:text-white transition-colors duration-300">

      <Navbar dark={dark} setDark={setDark} />

      <HomePage />

    </div>
  );
}

export default App;
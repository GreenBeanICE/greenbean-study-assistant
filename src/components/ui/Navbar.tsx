function Navbar({
  dark,
  setDark,
}: {
  dark: boolean;
  setDark: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  return (
    <header className="fixed top-0 left-0 w-full h-16 z-50 backdrop-blur-xl bg-white/80 dark:bg-black/70 border-b border-black/5 dark:border-white/10">

      <div className="h-full max-w-7xl mx-auto px-4 md:px-6 flex items-center justify-between">

        {/* Logo */}
        <div className="text-lg font-semibold tracking-tight">
          GreenBean
        </div>

        {/* 右侧 */}
        <div className="flex items-center gap-2">

          {/* 语言切换 */}
          <button className="px-3 py-1.5 rounded-full text-sm bg-black/5 dark:bg-white/10 hover:scale-105 transition">
            FR
          </button>

          {/* Dark mode */}
          <button
            onClick={() => setDark((prev) => !prev)}
            className="w-10 h-10 rounded-full bg-black/5 dark:bg-white/10 hover:scale-105 transition"
          >
            {dark ? "☀️" : "🌙"}
          </button>

          {/* Guest */}
          <button className="px-4 py-2 rounded-full text-sm hover:bg-black/5 dark:hover:bg-white/10 transition">
            Guest
          </button>

          {/* Login */}
          <button className="px-4 py-2 rounded-full text-sm bg-black text-white dark:bg-white dark:text-black hover:scale-[1.02] transition">
            Login
          </button>

        </div>
      </div>
    </header>
  );
}

export default Navbar;
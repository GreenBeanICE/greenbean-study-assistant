function Navbar({
  dark,
  setDark,
}: {
  dark: boolean;
  setDark: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  return (
    <header className="w-full fixed top-0 left-0 z-50 backdrop-blur-xl bg-white/60 dark:bg-black/40 border-b border-black/5 dark:border-white/10 transition">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">

        {/* Logo */}
        <div className="font-medium tracking-tight text-black dark:text-white">
          GreenBean
        </div>

        <div className="flex items-center gap-3">

          {/* 语言切换（法语） */}
          <button className="text-sm px-3 py-1.5 rounded-full bg-black/5 dark:bg-white/10 hover:opacity-80 transition">
            FR
          </button>

          {/* 深色模式切换 */}
          <button
            onClick={() => setDark(!dark)}
            className="text-sm px-3 py-1.5 rounded-full bg-black/5 dark:bg-white/10 hover:scale-105 active:scale-95 transition"
          >
            🌙
          </button>

        </div>
      </div>
    </header>
  );
}

export default Navbar;
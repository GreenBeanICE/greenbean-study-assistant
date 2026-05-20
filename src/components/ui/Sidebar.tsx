function Sidebar() {
  const items = [
    "📚 我的课程",
    "🧠 AI 工具",
    "📂 文件管理",
    "⭐ 收藏内容",
    "⚙️ 设置",
  ];

  return (
    <aside className="hidden md:flex w-64 flex-col border-r border-black/5 dark:border-white/10 px-4 py-6">

      {/* 标题 */}
      <div className="text-sm uppercase tracking-widest text-neutral-400 mb-6">
        Workspace
      </div>

      {/* 菜单 */}
      <div className="flex flex-col gap-2">

        {items.map((item) => (
          <button
            key={item}
            className="flex items-center px-4 py-3 rounded-2xl text-left hover:bg-black/5 dark:hover:bg-white/5 transition"
          >
            {item}
          </button>
        ))}

      </div>

    </aside>
  );
}

export default Sidebar;
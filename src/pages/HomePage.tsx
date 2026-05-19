import { motion } from "framer-motion";

function HomePage() {
  return (
    <div className="relative min-h-screen pt-24 overflow-hidden">

      <div className="absolute inset-0 bg-gradient-to-b from-white via-neutral-50 to-white dark:from-black dark:via-neutral-950 dark:to-black" />

      {/* 悬浮动效 */}
      <motion.div
        animate={{ y: [0, 30, 0] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-[-200px] left-[-150px] w-[500px] h-[500px] bg-emerald-300/20 blur-[180px] rounded-full"
      />

      <motion.div
        animate={{ y: [0, -40, 0] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-[-200px] right-[-150px] w-[500px] h-[500px] bg-teal-300/10 blur-[180px] rounded-full"
      />

      <div className="relative z-10 flex flex-col items-center px-6">

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center max-w-3xl"
        >
          <h1 className="text-5xl md:text-6xl font-semibold tracking-tight">
            GreenBean
          </h1>

          <p className="mt-6 text-lg text-neutral-500 dark:text-neutral-400 leading-relaxed">
            面向法国留学生的 AI 学习助手<br />
            理解课程 · 提取重点 · 智能问答
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.8 }}
          className="mt-16 w-full max-w-2xl"
        >
          <div className="rounded-3xl border border-black/10 dark:border-white/10 bg-white/60 dark:bg-white/5 backdrop-blur-xl p-8 shadow-sm">

            {/* 上传部分 */}
            <div className="h-64 rounded-2xl border border-dashed border-black/20 dark:border-white/10 flex items-center justify-center text-neutral-500 transition hover:scale-[1.01]">
              拖拽上传 支持 PDF / PPT / Word / 图片 格式
            </div>

            {/* 按钮 */}
            <div className="flex justify-center gap-4 mt-8">
              <button className="px-6 py-2 rounded-full bg-black text-white dark:bg-white dark:text-black text-sm hover:scale-[1.03] transition">
                选择文件
              </button>

              <button className="px-6 py-2 rounded-full border border-black/10 dark:border-white/10 text-sm hover:scale-[1.03] transition">
                开始解析
              </button>
            </div>

          </div>
        </motion.div>

        {/* 注释 */}
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="text-center text-neutral-400 dark:text-neutral-500 text-xs mt-8 leading-relaxed max-w-md"
        >
          上传后系统会先生成课程结构索引
          <br />
          可按章节选择需要 AI 深度解析的内容
        </motion.p>

      </div>
    </div>
  );
}

export default HomePage;
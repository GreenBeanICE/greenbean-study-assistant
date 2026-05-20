import { motion } from "framer-motion";
import Sidebar from "../components/ui/Sidebar";

function HomePage() {
  return (
    <div className="min-h-screen pt-16 bg-[#f5f5f7] dark:bg-[#0a0a0a] transition-colors duration-300">

      {/* 主布局 */}
      <div className="flex">

        {/* 左侧 Sidebar */}
        <Sidebar />

        {/* 主内容 */}
        <main className="flex-1 px-4 md:px-10 py-8">

          {/* 欢迎区域 */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-3xl md:text-5xl font-semibold tracking-tight">
              欢迎回来
            </h1>

            <p className="mt-4 text-neutral-500 dark:text-neutral-400 text-base md:text-lg leading-relaxed">
              GreenBean 帮助你理解法国大学课程内容，
              <br />
              自动整理知识结构并提供 AI 深度解析。
            </p>
          </motion.div>

          {/* 上传卡片 */}
          <motion.div
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.6 }}
            className="mt-10"
          >
            <div className="rounded-[32px] bg-white dark:bg-white/5 border border-black/5 dark:border-white/10 p-6 md:p-8 shadow-sm backdrop-blur-xl">

              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">

                {/* 左边 */}
                <div>
                  <h2 className="text-2xl font-semibold">
                    上传课程资料
                  </h2>

                  <p className="mt-3 text-neutral-500 dark:text-neutral-400 leading-relaxed">
                    支持 PDF / PPT / Word / 图片
                    <br />
                    自动生成课程结构与 AI 解析
                  </p>
                </div>

                {/* 右边按钮 */}
                <div className="flex flex-col sm:flex-row gap-3">

                  <button className="px-6 py-3 rounded-full bg-black text-white dark:bg-white dark:text-black hover:scale-[1.02] transition">
                    选择文件
                  </button>

                  <button className="px-6 py-3 rounded-full border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/5 transition">
                    开始解析
                  </button>

                </div>

              </div>

            </div>
          </motion.div>

          {/* Quick Actions */}
          <section className="mt-12">

            <h2 className="text-2xl font-semibold mb-5">
              Quick Actions
            </h2>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">

              {[
                "📄 AI 总结",
                "🧠 Quiz Generator",
                "🇫🇷 法语术语",
                "✨ 智能问答",
              ].map((item) => (
                <div
                  key={item}
                  className="rounded-3xl bg-white dark:bg-white/5 border border-black/5 dark:border-white/10 p-5 hover:scale-[1.02] transition cursor-pointer"
                >
                  <p className="font-medium">
                    {item}
                  </p>
                </div>
              ))}

            </div>
          </section>

          {/* Recent Files */}
          <section className="mt-12">

            <h2 className="text-2xl font-semibold mb-5">
              Recent Files
            </h2>

            <div className="space-y-4">

              {[
                "Macroéconomie Chapitre 2.pdf",
                "Analyse Mathématique.pptx",
                "Droit Civil Notes.docx",
              ].map((file) => (
                <div
                  key={file}
                  className="rounded-3xl bg-white dark:bg-white/5 border border-black/5 dark:border-white/10 p-5 flex items-center justify-between"
                >

                  <div>
                    <p className="font-medium">
                      {file}
                    </p>

                    <p className="text-sm text-neutral-500 mt-1">
                      最近打开
                    </p>
                  </div>

                  <button className="px-4 py-2 rounded-full text-sm bg-black text-white dark:bg-white dark:text-black">
                    打开
                  </button>

                </div>
              ))}

            </div>

          </section>

        </main>
      </div>
    </div>
  );
}

export default HomePage;
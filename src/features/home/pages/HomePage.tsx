import { useRef } from "react";
import { motion } from "framer-motion";
import UploadZone from "../components/UploadZone";
import { useI18n } from "../../../lib/i18n";

interface HomePageProps {
  onLogin: () => void;
}

function HomePage({ onLogin }: HomePageProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const workflowRef = useRef<HTMLDivElement>(null);
  const { t } = useI18n();

  const scrollToWorkflow = () => {
    workflowRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const scroll = (dir: "left" | "right") => {
    if (!scrollRef.current) return;
    const amount = 320;
    scrollRef.current.scrollBy({
      left: dir === "left" ? -amount : amount,
      behavior: "smooth",
    });
  };

  const features = [
    {
      title: t("feature1Title"),
      description: t("feature1Desc"),
      svg: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
      ),
    },
    {
      title: t("feature2Title"),
      description: t("feature2Desc"),
      svg: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      ),
    },
    {
      title: t("feature3Title"),
      description: t("feature3Desc"),
      svg: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      ),
    },
    {
      title: t("feature4Title"),
      description: t("feature4Desc"),
      svg: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      ),
    },
  ];

  const screenshots = [
    { label: t("screenshot1Label"), desc: t("screenshot1Desc"), gradient: "from-blue-400 to-indigo-500" },
    { label: t("screenshot2Label"), desc: t("screenshot2Desc"), gradient: "from-purple-400 to-pink-500" },
    { label: t("screenshot3Label"), desc: t("screenshot3Desc"), gradient: "from-emerald-400 to-teal-500" },
    { label: t("screenshot4Label"), desc: t("screenshot4Desc"), gradient: "from-amber-400 to-orange-500" },
    { label: t("screenshot5Label"), desc: t("screenshot5Desc"), gradient: "from-rose-400 to-red-500" },
  ];

  const steps = [
    {
      step: "01", title: t("step1Title"), desc: t("step1Desc"),
      svg: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
      ),
    },
    {
      step: "02", title: t("step2Title"), desc: t("step2Desc"),
      svg: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      ),
    },
    {
      step: "03", title: t("step3Title"), desc: t("step3Desc"),
      svg: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-[#f5f5f7] dark:bg-[#0a0a0a] transition-colors duration-300">
      {/* ============ Hero 区域 ============ */}
      <section className="pt-28 pb-20 md:pt-36 md:pb-28 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 md:gap-16 items-center">
            {/* 左侧文案 */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.7 }}
            >
              <span className="inline-block px-3.5 py-1 mb-5 text-[11px] font-medium tracking-[0.08em] text-neutral-500 dark:text-neutral-400 bg-black/5 dark:bg-white/10 rounded-full">
                {t("heroBadge")}
              </span>

              <h1 className="text-[2.6rem] md:text-[3.5rem] lg:text-[4rem] font-semibold tracking-tight leading-[1.08]">
                {t("heroTitle1")}
                <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400">
                  {t("heroTitle2")}
                </span>
              </h1>

              <p className="mt-5 text-base md:text-lg text-neutral-500 dark:text-neutral-400 leading-relaxed max-w-md">
                {t("heroDesc")}
              </p>

              <div className="mt-8 flex gap-3">
                <button
                  onClick={scrollToWorkflow}
                  className="px-7 py-3 rounded-full bg-black text-white dark:bg-white dark:text-black text-sm font-medium hover:opacity-85 transition shadow-lg shadow-black/10 dark:shadow-white/10"
                >
                  {t("heroCta")}
                </button>
                <button className="px-7 py-3 rounded-full border border-black/10 dark:border-white/20 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/5 transition">
                  {t("heroLearnMore")}
                </button>
              </div>
            </motion.div>

            {/* 右侧插图 */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.7, delay: 0.15 }}
              className="hidden md:block"
            >
              <div className="aspect-[4/3] rounded-[2.5rem] bg-gradient-to-br from-neutral-200 to-neutral-300 dark:from-neutral-800 dark:to-neutral-700 flex items-center justify-center overflow-hidden">
                <div className="text-center p-8">
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="0.8" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-400 dark:text-neutral-500 mx-auto opacity-50">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                    <line x1="8" y1="7" x2="16" y2="7" />
                    <line x1="8" y1="11" x2="14" y2="11" />
                  </svg>
                  <p className="mt-4 text-sm text-neutral-400 dark:text-neutral-500">
                    {t("heroImagePlaceholder")}
                  </p>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ============ 功能特性区域（横向布局） ============ */}
      <section id="features" className="py-20 md:py-28 px-4 bg-white/40 dark:bg-white/[0.02]">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6 }}
            className="mb-14"
          >
            <h2 className="text-[2rem] md:text-[2.8rem] font-semibold tracking-tight">
              {t("featuresTitle")}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400"> GreenBean</span>
              {t("featuresTitleSuffix")}
            </h2>
            <p className="mt-3 text-neutral-500 dark:text-neutral-400 max-w-lg">
              {t("featuresDesc")}
            </p>
          </motion.div>

          {/* 横向卡片布局 - 可横向滚动 */}
          <div className="relative">
            <div
              ref={scrollRef}
              className="flex gap-4 md:gap-5 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-hide"
              style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
            >
              {features.map((feature, idx) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-60px" }}
                  transition={{ delay: idx * 0.1, duration: 0.5 }}
                  className="min-w-[280px] md:min-w-[300px] flex-shrink-0 snap-start rounded-3xl bg-white dark:bg-white/5 border border-black/5 dark:border-white/10 p-7 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
                >
                  <div className="w-12 h-12 rounded-xl bg-black/5 dark:bg-white/10 flex items-center justify-center">
                    {feature.svg}
                  </div>
                  <h3 className="mt-5 text-lg font-semibold">{feature.title}</h3>
                  <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400 leading-relaxed">
                    {feature.description}
                  </p>
                </motion.div>
              ))}
            </div>

            {/* 左右滚动按钮 */}
            <button
              onClick={() => scroll("left")}
              className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-3 w-10 h-10 rounded-full bg-white dark:bg-neutral-800 border border-black/10 dark:border-white/10 shadow-lg flex items-center justify-center hover:scale-105 transition hidden md:flex"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6" />
              </svg>
            </button>
            <button
              onClick={() => scroll("right")}
              className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-3 w-10 h-10 rounded-full bg-white dark:bg-neutral-800 border border-black/10 dark:border-white/10 shadow-lg flex items-center justify-center hover:scale-105 transition hidden md:flex"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          </div>
        </div>
      </section>

      {/* ============ 宣传截图 / 快照区域（横向滑动） ============ */}
      <section id="screenshots" className="py-20 md:py-28 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6 }}
            className="mb-14"
          >
            <h2 className="text-[2rem] md:text-[2.8rem] font-semibold tracking-tight">
              {t("screenshotsTitle")}
            </h2>
            <p className="mt-3 text-neutral-500 dark:text-neutral-400 max-w-lg">
              {t("screenshotsDesc")}
            </p>
          </motion.div>

          {/* 横向滑动截图区域 */}
          <div className="relative">
            <div
              className="flex gap-5 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-hide"
              style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
            >
              {screenshots.map((item, idx) => (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-60px" }}
                  transition={{ delay: idx * 0.1, duration: 0.5 }}
                  className="min-w-[280px] md:min-w-[380px] lg:min-w-[420px] flex-shrink-0 snap-start rounded-[2rem] bg-white dark:bg-white/5 border border-black/5 dark:border-white/10 overflow-hidden group"
                >
                  {/* 截图占位区域 */}
                  <div className={`aspect-[16/10] bg-gradient-to-br ${item.gradient} flex items-center justify-center`}>
                    <div className="text-center text-white/60">
                      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="0.8" strokeLinecap="round" strokeLinejoin="round" className="mx-auto opacity-60">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                        <circle cx="8.5" cy="8.5" r="1.5" />
                        <polyline points="21 15 16 10 5 21" />
                      </svg>
                      <p className="mt-2 text-xs text-white/40">{t("screenshotPlaceholder")}</p>
                    </div>
                  </div>
                  <div className="p-5">
                    <h3 className="font-semibold">{item.label}</h3>
                    <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
                      {item.desc}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============ 上传流程区域 + UploadZone ============ */}
      <section id="workflow" ref={workflowRef} className="py-20 md:py-28 px-4 bg-white/40 dark:bg-white/[0.02]">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6 }}
            className="mb-14"
          >
            <h2 className="text-[2rem] md:text-[2.8rem] font-semibold tracking-tight">
              {t("workflowTitle")}
            </h2>
            <p className="mt-3 text-neutral-500 dark:text-neutral-400 max-w-lg">
              {t("workflowDesc")}
            </p>
          </motion.div>

          {/* 三步流程（横向） */}
          <div className="grid md:grid-cols-3 gap-8 md:gap-12 mb-16">
            {steps.map((item, idx) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ delay: idx * 0.15, duration: 0.5 }}
                className="flex md:flex-col items-center md:text-center gap-5 md:gap-0"
              >
                <span className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-full bg-black text-white dark:bg-white dark:text-black">
                  {item.svg}
                </span>
                <div>
                  <span className="text-xs font-medium text-neutral-400 tracking-wider">
                    {t("stepLabel")} {item.step}
                  </span>
                  <h3 className="mt-1 text-lg font-semibold">{item.title}</h3>
                  <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400 leading-relaxed">
                    {item.desc}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>

          {/* UploadZone 区域 */}
          <div>
            <UploadZone onLogin={onLogin} />
          </div>
        </div>
      </section>

      {/* ============ 底部 CTA ============ */}
      <section className="py-24 md:py-32 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-[2rem] md:text-[3.5rem] font-semibold tracking-tight">
              {t("ctaTitle")}
            </h2>
            <p className="mt-4 text-neutral-500 dark:text-neutral-400 max-w-lg mx-auto">
              {t("ctaDesc")}
            </p>
            <button
              onClick={scrollToWorkflow}
              className="mt-8 px-10 py-4 rounded-full bg-black text-white dark:bg-white dark:text-black font-medium text-base hover:opacity-85 transition shadow-xl shadow-black/10 dark:shadow-white/10"
            >
              {t("ctaButton")}
            </button>
          </motion.div>
        </div>
      </section>

      {/* ============ Footer ============ */}
      <footer className="py-8 px-4 border-t border-black/5 dark:border-white/10">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-neutral-400">
          <span>&copy; 2025 GreenBean Study Assistant</span>
          <div className="flex gap-6">
            <span className="hover:text-neutral-600 dark:hover:text-neutral-300 cursor-pointer transition">{t("footerAbout")}</span>
            <span className="hover:text-neutral-600 dark:hover:text-neutral-300 cursor-pointer transition">{t("footerPrivacy")}</span>
            <span className="hover:text-neutral-600 dark:hover:text-neutral-300 cursor-pointer transition">{t("footerTerms")}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default HomePage;
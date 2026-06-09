import { useRef } from "react";
import { motion } from "framer-motion";
import UploadZone from "../components/UploadZone";
import { useI18n } from "../../../lib/i18n";
import { SVG_ICONS, SCREENSHOT_GRADIENTS } from "../constants";

/** 首页宣传页面属性 */
interface HomePageProps {
  /** 用户触发登录流程时的回调函数 */
  onLogin: () => void;
}

function HomePage({ onLogin }: HomePageProps) {
  // 功能卡片横向滚动容器的 ref
  const scrollRef = useRef<HTMLDivElement>(null);
  // "三步搞定课程解析"流程区域的 ref，用于点击按钮后精确滚动定位
  const workflowRef = useRef<HTMLDivElement>(null);
  const { t } = useI18n();

  // 滚动到上传流程区域（"三步搞定课程解析"标题）
  const scrollToWorkflow = () => {
    workflowRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  // 功能卡片区域的左右横向滚动
  const scroll = (dir: "left" | "right") => {
    if (!scrollRef.current) return;
    const amount = 320;
    scrollRef.current.scrollBy({
      left: dir === "left" ? -amount : amount,
      behavior: "smooth",
    });
  };

  // 四个功能特性卡片：文档解析、AI 分析、知识结构化、智能问答
  const features = [
    { title: t("feature1Title"), description: t("feature1Desc"), svg: SVG_ICONS.document },
    { title: t("feature2Title"), description: t("feature2Desc"), svg: SVG_ICONS.brain },
    { title: t("feature3Title"), description: t("feature3Desc"), svg: SVG_ICONS.trending },
    { title: t("feature4Title"), description: t("feature4Desc"), svg: SVG_ICONS.messageCircle },
  ];

  // 五个宣传截图占位卡片
  const screenshots = [
    { label: t("screenshot1Label"), desc: t("screenshot1Desc") },
    { label: t("screenshot2Label"), desc: t("screenshot2Desc") },
    { label: t("screenshot3Label"), desc: t("screenshot3Desc") },
    { label: t("screenshot4Label"), desc: t("screenshot4Desc") },
    { label: t("screenshot5Label"), desc: t("screenshot5Desc") },
  ];

  // 三步上传流程：上传文件、自动解析、深度互动
  const steps = [
    { step: "01", title: t("step1Title"), desc: t("step1Desc"), svg: SVG_ICONS.upload },
    { step: "02", title: t("step2Title"), desc: t("step2Desc"), svg: SVG_ICONS.trending },
    { step: "03", title: t("step3Title"), desc: t("step3Desc"), svg: SVG_ICONS.messageCircle },
  ];

  return (
    <div className="min-h-screen bg-[#f5f5f7] dark:bg-[#0a0a0a] transition-colors duration-300">
      {/* 页面顶部 Hero 区域：左文右图两栏布局 */}
      <section className="pt-28 pb-20 md:pt-36 md:pb-28 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 md:gap-16 items-center">
            <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.7 }}>
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
                <button onClick={scrollToWorkflow} className="px-7 py-3 rounded-full bg-black text-white dark:bg-white dark:text-black text-sm font-medium hover:opacity-85 transition shadow-lg shadow-black/10 dark:shadow-white/10">
                  {t("heroCta")}
                </button>
                <button className="px-7 py-3 rounded-full border border-black/10 dark:border-white/20 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/5 transition">
                  {t("heroLearnMore")}
                </button>
              </div>
            </motion.div>
            <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.7, delay: 0.15 }} className="hidden md:block">
              <div className="aspect-[4/3] rounded-[2.5rem] bg-gradient-to-br from-neutral-200 to-neutral-300 dark:from-neutral-800 dark:to-neutral-700 flex items-center justify-center overflow-hidden">
                <div className="text-center p-8">
                  <div className="text-neutral-400 dark:text-neutral-500 mx-auto opacity-50">{SVG_ICONS.bookOpen}</div>
                  <p className="mt-4 text-sm text-neutral-400 dark:text-neutral-500">{t("heroImagePlaceholder")}</p>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* 功能特性区域：横向可滑动的四个产品功能卡片 */}
      <section id="features" className="py-20 md:py-28 px-4 bg-white/40 dark:bg-white/[0.02]">
        <div className="max-w-6xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-80px" }} transition={{ duration: 0.6 }} className="mb-14">
            <h2 className="text-[2rem] md:text-[2.8rem] font-semibold tracking-tight">
              {t("featuresTitle")}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400"> GreenBean</span>
              {t("featuresTitleSuffix")}
            </h2>
            <p className="mt-3 text-neutral-500 dark:text-neutral-400 max-w-lg">{t("featuresDesc")}</p>
          </motion.div>
          <div className="relative">
            <div ref={scrollRef} className="flex gap-4 md:gap-5 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-hide" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
              {features.map((feature, idx) => (
                <motion.div key={feature.title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-60px" }} transition={{ delay: idx * 0.1, duration: 0.5 }}
                  className="min-w-[280px] md:min-w-[300px] flex-shrink-0 snap-start rounded-3xl bg-white dark:bg-white/5 border border-black/5 dark:border-white/10 p-7 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
                  <div className="w-12 h-12 rounded-xl bg-black/5 dark:bg-white/10 flex items-center justify-center">{feature.svg}</div>
                  <h3 className="mt-5 text-lg font-semibold">{feature.title}</h3>
                  <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400 leading-relaxed">{feature.description}</p>
                </motion.div>
              ))}
            </div>
            <button onClick={() => scroll("left")} className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-3 w-10 h-10 rounded-full bg-white dark:bg-neutral-800 border border-black/10 dark:border-white/10 shadow-lg flex items-center justify-center hover:scale-105 transition hidden md:flex">{SVG_ICONS.chevronLeft}</button>
            <button onClick={() => scroll("right")} className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-3 w-10 h-10 rounded-full bg-white dark:bg-neutral-800 border border-black/10 dark:border-white/10 shadow-lg flex items-center justify-center hover:scale-105 transition hidden md:flex">{SVG_ICONS.chevronRight}</button>
          </div>
        </div>
      </section>

      {/* 宣传截图区域：横向滑动的产品截图占位卡片 */}
      <section id="screenshots" className="py-20 md:py-28 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-80px" }} transition={{ duration: 0.6 }} className="mb-14">
            <h2 className="text-[2rem] md:text-[2.8rem] font-semibold tracking-tight">{t("screenshotsTitle")}</h2>
            <p className="mt-3 text-neutral-500 dark:text-neutral-400 max-w-lg">{t("screenshotsDesc")}</p>
          </motion.div>
          <div className="relative">
            <div className="flex gap-5 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-hide" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
              {screenshots.map((item, idx) => (
                <motion.div key={item.label} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-60px" }} transition={{ delay: idx * 0.1, duration: 0.5 }}
                  className="min-w-[280px] md:min-w-[380px] lg:min-w-[420px] flex-shrink-0 snap-start rounded-[2rem] bg-white dark:bg-white/5 border border-black/5 dark:border-white/10 overflow-hidden group">
                  <div className={`aspect-[16/10] bg-gradient-to-br ${SCREENSHOT_GRADIENTS[idx]} flex items-center justify-center`}>
                    <div className="text-center text-white/60">
                      <div className="mx-auto opacity-60">{SVG_ICONS.image}</div>
                      <p className="mt-2 text-xs text-white/40">{t("screenshotPlaceholder")}</p>
                    </div>
                  </div>
                  <div className="p-5">
                    <h3 className="font-semibold">{item.label}</h3>
                    <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">{item.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 上传流程区域：三步流程说明 + 拖拽上传组件 */}
      <section id="workflow" ref={workflowRef} className="py-20 md:py-28 px-4 bg-white/40 dark:bg-white/[0.02]">
        <div className="max-w-6xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-80px" }} transition={{ duration: 0.6 }} className="mb-14">
            <h2 className="text-[2rem] md:text-[2.8rem] font-semibold tracking-tight">{t("workflowTitle")}</h2>
            <p className="mt-3 text-neutral-500 dark:text-neutral-400 max-w-lg">{t("workflowDesc")}</p>
          </motion.div>
          <div className="grid md:grid-cols-3 gap-8 md:gap-12 mb-16">
            {steps.map((item, idx) => (
              <motion.div key={item.step} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-60px" }} transition={{ delay: idx * 0.15, duration: 0.5 }}
                className="flex md:flex-col items-center md:text-center gap-5 md:gap-0">
                <span className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-full bg-black text-white dark:bg-white dark:text-black">{item.svg}</span>
                <div>
                  <span className="text-xs font-medium text-neutral-400 tracking-wider">{t("stepLabel")} {item.step}</span>
                  <h3 className="mt-1 text-lg font-semibold">{item.title}</h3>
                  <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400 leading-relaxed">{item.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
          <div><UploadZone onLogin={onLogin} /></div>
        </div>
      </section>

      {/* 底部 CTA 区域：引导用户开始使用 */}
      <section className="py-24 md:py-32 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }}>
            <h2 className="text-[2rem] md:text-[3.5rem] font-semibold tracking-tight">{t("ctaTitle")}</h2>
            <p className="mt-4 text-neutral-500 dark:text-neutral-400 max-w-lg mx-auto">{t("ctaDesc")}</p>
            <button onClick={scrollToWorkflow} className="mt-8 px-10 py-4 rounded-full bg-black text-white dark:bg-white dark:text-black font-medium text-base hover:opacity-85 transition shadow-xl shadow-black/10 dark:shadow-white/10">
              {t("ctaButton")}
            </button>
          </motion.div>
        </div>
      </section>

      {/* 页面底部：版权信息和链接 */}
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
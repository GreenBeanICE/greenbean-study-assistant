import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";

/** 欢迎/启动页属性 */
interface SplashPageProps {
  /** 跳转到工作区的回调函数 */
  onStart: () => void;
}

/** 三秒倒计时后自动跳转的欢迎启动页 */
function SplashPage({ onStart }: SplashPageProps) {
  const [countdown, setCountdown] = useState(3);

  useEffect(() => {
    if (countdown <= 0) {
      onStart();
      return;
    }
    const timer = setTimeout(() => setCountdown((prev) => prev - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown, onStart]);

  const handleSkip = useCallback(() => {
    onStart();
  }, [onStart]);

  return (
    <div className="min-h-screen bg-[#f5f5f7] transition-colors duration-300 flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
        className="text-center px-6"
      >
        {/* Logo / 品牌 */}
        <div className="mb-6 inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/20">
          <span className="text-white text-3xl font-bold">G</span>
        </div>

        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-neutral-800">
          GreenBean Study Assistant
        </h1>

        <p className="mt-3 text-neutral-500 max-w-md mx-auto text-sm md:text-base">
          你的 AI 课程资料助手 —— 导入、解析、理解、掌握。
        </p>

        {/* 进度指示 */}
        <div className="mt-10 flex flex-col items-center gap-4">
          <div className="relative w-12 h-12">
            <svg className="w-12 h-12 -rotate-90" viewBox="0 0 36 36">
              <circle cx="18" cy="18" r="16" fill="none" stroke="currentColor" strokeWidth="2"
                className="text-black/10" />
              <motion.circle cx="18" cy="18" r="16" fill="none" stroke="currentColor" strokeWidth="2"
                className="text-blue-600"
                strokeDasharray="100.53"
                initial={{ strokeDashoffset: 100.53 }}
                animate={{ strokeDashoffset: 100.53 * (1 - countdown / 3) }}
                transition={{ duration: 1, ease: "linear" }}
                strokeLinecap="round" />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-neutral-600">
              {countdown}
            </span>
          </div>
          <p className="text-xs text-neutral-400">
            {countdown > 0 ? `即将进入工作区 (${countdown}s)` : "正在进入..."}
          </p>
        </div>

        {/* 跳过按钮 */}
        <button
          onClick={handleSkip}
          className="mt-8 px-8 py-2.5 rounded-full bg-black text-white text-sm font-medium hover:opacity-85 transition shadow-lg shadow-black/10"
        >
          跳过 · 立即进入
        </button>
      </motion.div>
    </div>
  );
}

export default SplashPage;
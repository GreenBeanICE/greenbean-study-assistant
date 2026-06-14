import { motion } from "framer-motion";

interface MungBeanSplashProps {
  onSkip?: () => void;
  className?: string;
}

const EMERALD_GRADIENT = "from-emerald-300/60 via-green-400/40 to-sky-300/50";
const CRYSTAL_1 = "bg-emerald-400/70";
const CRYSTAL_2 = "bg-cyan-300/60";
const CRYSTAL_3 = "bg-lime-300/60";
export default function MungBeanSplash({ onSkip, className = "" }: MungBeanSplashProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
      className={`fixed inset-0 z-[100] flex items-center justify-center bg-white select-none ${className}`}
    >
      {onSkip && (
        <button
          onClick={onSkip}
          className="fixed top-5 right-5 z-10 px-5 py-2 rounded-full text-sm font-medium
                     text-neutral-400
                     border border-neutral-300
                     hover:text-neutral-600
                     hover:border-neutral-400
                     transition-colors duration-200 cursor-pointer"
        >
          跳过
        </button>
      )}

      <div className="flex flex-col items-center gap-4">
        <div className="relative w-16 h-20 flex items-center justify-center">
          {/* 背景光晕 */}
          <motion.div
            className={`absolute rounded-full bg-gradient-to-br ${EMERALD_GRADIENT}`}
            style={{ width: 52, height: 52, left: -8, bottom: 0 }}
            animate={{ scale: [0.9, 1.18, 0.9], opacity: [0.5, 0.9, 0.5] }}
            transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut", delay: 0 }}
          />
          <motion.div
            className="absolute rounded-full bg-gradient-to-br from-sky-300/50 to-blue-300/35"
            style={{ width: 46, height: 46, right: -6, top: -6 }}
            animate={{ scale: [0.85, 1.22, 0.85], opacity: [0.4, 0.85, 0.4] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 0.3 }}
          />
          <motion.div
            className={`absolute rounded-full bg-gradient-to-br ${EMERALD_GRADIENT}`}
            style={{ width: 28, height: 28, right: 4, bottom: 2 }}
            animate={{ scale: [0.9, 1.25, 0.9], opacity: [0.3, 0.7, 0.3] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut", delay: 0.8 }}
          />

          {/* 马天尼杯 + 冰沙 */}
          <div className="relative z-10">
            <svg width="66" height="86" viewBox="0 0 66 86" fill="none">
              <defs>
                <linearGradient id="smGrad" x1="0" y1="1" x2="0" y2="0">
                  <stop offset="0%" stopColor="#6cb660" />
                  <stop offset="35%" stopColor="#a8e6a3" />
                  <stop offset="65%" stopColor="#d6f0d0" />
                  <stop offset="100%" stopColor="#f5faf0" />
                </linearGradient>
              </defs>

              {/* 杯身 */}
              <path
                d="M7 6 Q9 10 10 14 L29 62 Q32 65 33 65 Q34 65 37 62 L56 14 Q57 10 59 6 Z"
                fill="rgba(255,255,255,0.15)"
                stroke="rgba(0,0,0,0.06)"
                strokeWidth="0.5"
              />
              {/* 杯口 */}
              <ellipse
                cx="33" cy="6" rx="26" ry="4.5"
                fill="rgba(255,255,255,0.2)"
                stroke="rgba(0,0,0,0.06)"
                strokeWidth="0.5"
              />
              {/* 杯柱 */}
              <rect x="30" y="65" width="6" height="16" rx="1.5" fill="rgba(0,0,0,0.04)" stroke="rgba(0,0,0,0.06)" strokeWidth="0.4" />
              {/* 杯座 */}
              <ellipse cx="33" cy="83" rx="16" ry="3" fill="rgba(0,0,0,0.03)" stroke="rgba(0,0,0,0.06)" strokeWidth="0.4" />
              {/* 玻璃高光 */}
              <path d="M14 16 Q16 20 17 26 L22 44" stroke="rgba(255,255,255,0.2)" strokeWidth="1.2" strokeLinecap="round" fill="none" />

              {/* 冰沙整体 */}
              <path
                d="
                  M7 6
                  L29 62 Q32 64 33 64 Q34 64 36 62 L57 6
                  C58 4 58 0 55 -2 C52 -4 44 -5 33 -5 C22 -5 14 -4 11 -2 C8 0 8 4 7 6
                  Z
                "
                fill="url(#smGrad)"
                opacity="0.94"
              />
              {/* 顶部高光 */}
              <motion.ellipse
                cx="30" cy="-4" rx="14" ry="2.5"
                fill="rgba(255,255,255,0.3)"
                animate={{ scaleY: [1, 1.08, 1] }}
                transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
                style={{ transformOrigin: "30px -4px" }}
              />

              {/* 冰沙绵密颗粒 */}
              {[
                [18, 18], [24, 22], [33, 20], [28, 32], [40, 28],
                [22, 34], [32, 28], [16, 30], [42, 32], [26, 42],
                [38, 40], [30, 38], [20, 24], [44, 30], [36, 48],
                [32, 42], [24, 32], [38, 36], [20, 36], [34, 46],
                [14, 10], [22, 6], [38, 5], [46, 8], [52, 10],
                [18, 2], [42, 2], [28, -1], [36, -2], [48, 4],
              ].map(([cx, cy], i) => (
                <circle key={`g-${i}`} cx={cx} cy={cy} r="0.8" fill="rgba(255,255,255,0.25)" />
              ))}

              {/* 飞溅粒子 */}
              <motion.circle cx="10" cy="2" r="1.2" fill="#f5faf0"
                animate={{ y: [-1, -3, -1], opacity: [0.5, 0.1, 0.5] }}
                transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
              />
              <motion.circle cx="55" cy="3" r="1" fill="#e6f5e0"
                animate={{ y: [-1, -2.5, -1], opacity: [0.4, 0.1, 0.4] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.6 }}
              />
            </svg>

            {/* 四周闪烁小圆形 */}
            <motion.div
              className={`absolute w-1.5 h-1.5 rounded-full ${CRYSTAL_1}`}
              style={{ left: -5, top: 6 }}
              animate={{ scale: [0.6, 1.3, 0.6], opacity: [0.3, 0.9, 0.3] }}
              transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut", delay: 0 }}
            />
            <motion.div
              className={`absolute w-1.5 h-1.5 rounded-full ${CRYSTAL_2}`}
              style={{ right: -4, top: 22 }}
              animate={{ scale: [0.6, 1.3, 0.6], opacity: [0.3, 0.9, 0.3] }}
              transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut", delay: 0.6 }}
            />
            <motion.div
              className={`absolute w-1 h-1 rounded-full ${CRYSTAL_3}`}
              style={{ right: -2, bottom: 8 }}
              animate={{ scale: [0.6, 1.3, 0.6], opacity: [0.3, 0.9, 0.3] }}
              transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut", delay: 1.1 }}
            />
          </div>
        </div>

        <p className="text-xs tracking-[0.15em] text-neutral-300 animate-pulse">
          GreenBean Study Assistant
        </p>
      </div>
    </motion.div>
  );
}
/* v8 ignore start */
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
/* v8 ignore stop */

interface MungBeanSplashProps {
  onSkip?: () => void;
  className?: string;
}

export default function MungBeanSplash({ onSkip, className = "" }: MungBeanSplashProps) {
  const [phase, setPhase] = useState<"dots" | "welcome" | "subtitle">("dots");

  useEffect(() => {
    const t1 = setTimeout(() => setPhase("welcome"), 800);
    const t2 = setTimeout(() => setPhase("subtitle"), 1700);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, []);

  useEffect(() => {
    if (!onSkip) {
      return;
    }
    const timer = setTimeout(() => onSkip(), 3800);
    return () => clearTimeout(timer);
  }, [onSkip]);

  const combinedClassName = ["fixed inset-0 z-[100] flex items-center justify-center bg-white select-none", className].filter(Boolean).join(" ");

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
      className={combinedClassName}
    >

      <div className="flex flex-col items-center" style={{ transform: "translateY(-2rem)" }}>
        <div className="relative w-80 h-48 flex items-center justify-center">
          <motion.div
            className="absolute rounded-full bg-gradient-to-br from-emerald-300/60 via-green-400/40 to-sky-300/50"
            style={{ width: 80, height: 80, left: "15%", top: "25%" }}
            initial={{ opacity: 0, scale: 0.6 }}
            animate={{ opacity: [0.5, 0.9, 0.5], scale: [0.9, 1.18, 0.9] }}
            transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute rounded-full bg-gradient-to-br from-sky-300/50 to-blue-300/35"
            style={{ width: 60, height: 60, right: "18%", top: "10%" }}
            initial={{ opacity: 0, scale: 0.6 }}
            animate={{ opacity: [0.4, 0.85, 0.4], scale: [0.85, 1.22, 0.85] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 0.3 }}
          />
          <motion.div
            className="absolute rounded-full bg-gradient-to-br from-emerald-300/60 via-green-400/40 to-sky-300/50"
            style={{ width: 40, height: 40, right: "25%", bottom: "10%" }}
            initial={{ opacity: 0, scale: 0.6 }}
            animate={{ opacity: [0.3, 0.7, 0.3], scale: [0.9, 1.25, 0.9] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut", delay: 0.8 }}
          />

          <AnimatePresence mode="wait">
            {phase !== "dots" && (
              <motion.div
                key="welcome"
                className="relative z-10"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
              >
                <span
                  className="text-neutral-800 text-4xl sm:text-5xl font-bold select-none tracking-[0.12em]"
                  style={{ writingMode: "horizontal-tb", whiteSpace: "nowrap" }}
                >
                  欢迎
                </span>
              </motion.div>
            )}
          </AnimatePresence>

          <motion.div
            className="absolute w-1.5 h-1.5 rounded-full bg-emerald-400/70"
            style={{ left: "20%", top: "30%" }}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0 }}
          />
          <motion.div
            className="absolute w-1.5 h-1.5 rounded-full bg-cyan-300/60"
            style={{ right: "22%", top: "35%" }}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          />
          <motion.div
            className="absolute w-1 h-1 rounded-full bg-lime-300/60"
            style={{ right: "28%", bottom: "20%" }}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          />
        </div>

        <AnimatePresence>
          {phase === "subtitle" && (
            <motion.p
              key="subtitle"
              className="text-sm tracking-[0.18em] text-neutral-400 font-light"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.15, ease: "easeOut" }}
            >
              GreenBean Study Assistant
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
import { motion, AnimatePresence } from "framer-motion";
import { useI18n } from "../../../lib/i18n";

interface LoginModalProps {
  open: boolean;
  onClose: () => void;
}

export default function LoginModal({ open, onClose }: LoginModalProps) {
  const { t } = useI18n();

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* 遮罩层 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* 浮框 */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="w-full max-w-sm rounded-3xl bg-white dark:bg-neutral-900 border border-black/5 dark:border-white/10 shadow-2xl p-8">
              {/* 图标 */}
              <div className="w-14 h-14 mx-auto rounded-full bg-black/5 dark:bg-white/10 flex items-center justify-center">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-black dark:text-white"
                >
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>

              <h2 className="mt-5 text-xl font-semibold text-center tracking-tight">
                {t("loginTitle")}
              </h2>
              <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400 text-center leading-relaxed">
                {t("loginDesc")}
              </p>

              <div className="mt-7 space-y-3">
                <button className="w-full py-3 rounded-full bg-black text-white dark:bg-white dark:text-black font-medium text-sm hover:opacity-85 transition">
                  {t("loginContinue")}
                </button>
                <button
                  onClick={onClose}
                  className="w-full py-3 rounded-full border border-black/10 dark:border-white/10 text-sm font-medium hover:bg-black/5 dark:hover:bg-white/5 transition"
                >
                  {t("loginLater")}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
import { useState, useRef, type DragEvent } from "react";
import { motion } from "framer-motion";
import { useI18n } from "../../../lib/i18n";
import { SVG_ICONS, SUPPORTED_FORMATS } from "../constants";

interface UploadZoneProps {
  onLogin: () => void;
}

export default function UploadZone({ onLogin }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { t } = useI18n();

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      setFileName(file.name);
      onLogin();
    }
  };

  const handleClick = () => {
    // 点击弹出登录提示，后续接入真实 auth 后可在此判断是否已登录
    onLogin();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 25 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15, duration: 0.6 }}
    >
      <div
        role="button"
        tabIndex={0}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") handleClick(); }}
        className={`
          relative cursor-pointer rounded-[32px] border-2 border-dashed p-8 md:p-10
          transition-all duration-300
          ${
            dragging
              ? "border-black dark:border-white bg-black/5 dark:bg-white/10 scale-[1.01]"
              : "border-black/10 dark:border-white/10 bg-white dark:bg-white/5 hover:border-black/30 dark:hover:border-white/30"
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.pptx,.txt,.md,.jpg,.jpeg,.png,.webp"
          className="hidden"
          onChange={handleFileChange}
        />

        <div className="text-center">
          {/* 上传图标 */}
          <div className="w-16 h-16 mx-auto rounded-full bg-black/5 dark:bg-white/10 flex items-center justify-center">
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-black dark:text-white"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>

          <p className="mt-4 text-lg font-semibold tracking-tight">
            {fileName ? fileName : t("uploadPrompt")}
          </p>

          <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
            {t("uploadFormat")}
          </p>

          {/* 文件格式列表 */}
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {SUPPORTED_FORMATS.map((fmt) => (
              <span
                key={fmt.ext}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-black/5 dark:bg-white/10 text-neutral-600 dark:text-neutral-300"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                {fmt.ext}
                <span className="text-neutral-400 dark:text-neutral-500">
                  {t(fmt.descKey)}
                </span>
              </span>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
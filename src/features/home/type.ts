/** 功能特性卡片 */
export interface FeatureItem {
  title: string;
  description: string;
  svg: React.ReactNode;
}

/** 宣传截图占位项 */
export interface ScreenshotPlaceholder {
  label: string;
  desc: string;
  gradient: string;
}

/** 上传流程状态 */
export type UploadFlowStatus = "idle" | "login-prompt" | "uploading" | "success";
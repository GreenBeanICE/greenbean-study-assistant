import type { FileType, Folder } from "./type";

export const DEFAULT_FOLDERS: Folder[] = [
  { key: "course", label: "课程资料" },
  { key: "exam", label: "考试复习" },
  { key: "thesis", label: "论文参考" },
];

export function createFileId(): string {
  const array = new Uint32Array(1);
  crypto.getRandomValues(array);
  return `f_${array[0].toString(36).slice(0, 7)}`;
}

export function getFileType(fileName: string): FileType {
  const ext = fileName.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "PDF";
  if (ext === "doc" || ext === "docx") return "DOC";
  if (ext === "ppt" || ext === "pptx") return "PPT";
  if (["png", "jpg", "jpeg", "webp"].includes(ext ?? "")) return "IMG";
  if (ext === "md") return "MD";
  return "TXT";
}

export function formatFileSize(bytes: number): string {
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

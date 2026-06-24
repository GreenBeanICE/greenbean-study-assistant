/**
 * 文档 API 封装 —— 对 apiClient 的薄封装。
 *
 * 所有函数通过相对路径 /api/documents/... 访问后端，
 * 开发期由 vite proxy 转发（见 vite.config.ts server.proxy），
 * 生产环境需由部署层或 Tauri 桥接处理路由。
 */
import { request, uploadFile } from "../../../lib/apiClient";
import type {
  DocumentDetail,
  DocumentSummary,
  DocumentUploadResponse,
} from "../../../types/document";

/**
 * 上传文档并触发后端解析流水线。
 * @param file   要上传的文件对象
 * @param workspaceId  可选的工作区 ID，不传则后端使用默认值
 */
export async function uploadDocument(
  file: File,
  workspaceId?: string,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (workspaceId) formData.append("workspace_id", workspaceId);
  return uploadFile("/documents/upload", formData);
}

/** 获取文档详情（含解析出的 DocumentUnit 列表） */
export async function getDocumentDetail(
  id: string,
): Promise<DocumentDetail> {
  return request(`/documents/${id}`);
}

/** 按 workspace 获取文档列表 */
export async function listDocuments(
  workspaceId: string,
): Promise<DocumentSummary[]> {
  return request(`/documents?workspace_id=${encodeURIComponent(workspaceId)}`);
}

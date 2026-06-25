/**
 * Provider 配置 API 封装 —— 对 apiClient 的薄封装。
 * 相对路径 /api/providers/... 由 vite proxy 转发到 Python 后端。
 */
import { request } from "../../../lib/apiClient";
import type {
  ActivateResponse,
  ProviderConfig,
  ProviderPayload,
  Purpose,
} from "../types";

export function listProviders(purpose?: Purpose): Promise<ProviderConfig[]> {
  const query = purpose ? `?purpose=${purpose}` : "";
  return request(`/providers${query}`);
}

export function createProvider(payload: ProviderPayload): Promise<ProviderConfig> {
  return request("/providers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateProvider(
  id: string,
  payload: Partial<ProviderPayload>,
): Promise<ProviderConfig> {
  return request(`/providers/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteProvider(id: string): Promise<boolean> {
  return request(`/providers/${id}`, { method: "DELETE" });
}

export function activateProvider(id: string): Promise<ActivateResponse> {
  return request(`/providers/${id}/activate`, { method: "POST" });
}

export function getActiveProvider(purpose: Purpose): Promise<ActivateResponse> {
  return request(`/providers/active?purpose=${purpose}`);
}

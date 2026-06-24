/**
 * 前端 API 客户端 —— 统一请求封装。
 *
 * 【开发期】
 *   API_BASE = "/api"，由 vite.config.ts 的 server.proxy 将 /api 请求
 *   转发到 Python 后端（uvicorn 默认 http://localhost:8000）。
 *   `npm run dev` 启动时代理自动生效，前端代码无需硬编码后端地址。
 *
 * 【生产期】
 *   Tauri 桌面端：需由 Tauri sidecar 或部署层将 /api 路由指向本机服务，
 *   或根据环境变量替换 API_BASE。
 *   Web 部署：可通过 nginx/Caddy 反向代理将 /api 指向后端，保持前端代码不变。
 */
const API_BASE = "/api";

/** 后端统一响应结构（见 document_controller.py 返回格式） */
interface ApiResponse<T> {
  code: number;
  data: T;
  message?: string;
}

function normalizeErrorDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        if (item && typeof item === "object") {
          const loc = Array.isArray((item as { loc?: unknown }).loc)
            ? (item as { loc: unknown[] }).loc.join(".")
            : "unknown";
          const msg = typeof (item as { msg?: unknown }).msg === "string"
            ? (item as { msg: string }).msg
            : JSON.stringify(item);
          return `${loc}: ${msg}`;
        }

        return String(item);
      })
      .join("; ");
  }

  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }

  return fallback;
}

/**
 * 通用请求：拼接 /api 前缀 → 发起 fetch → 解包 { code, data }。
 * 非 2xx 或业务码非 200 时抛出可读异常。
 */
export async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = normalizeErrorDetail((body as { detail?: unknown }).detail, detail);
    } catch {
      /* 响应体非 JSON，忽略 */
    }
    throw new Error(`请求失败 (${res.status}): ${detail}`);
  }

  const json = (await res.json()) as ApiResponse<T>;
  if (json.code !== 200) {
    throw new Error(json.message ?? `业务错误 ${json.code}`);
  }
  return json.data;
}

/**
 * 文件上传专用：POST FormData。
 * 不设置 Content-Type，让浏览器自动拼 boundary。
 */
export async function uploadFile<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  return request<T>(path, { method: "POST", body: formData });
}

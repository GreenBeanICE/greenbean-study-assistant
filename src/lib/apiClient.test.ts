import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// apiClient 通过相对路径 /api 访问后端，开发期由 vite proxy 转发到 localhost:8000。
// 此处只验证客户端的解包与错误处理契约，不涉及真实网络。
import { request, uploadFile } from "./apiClient";

describe("apiClient.request", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("成功响应时解包 { code, data } 并返回 data", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ code: 200, data: { id: "doc1" } }), { status: 200 }),
    ) as unknown as typeof fetch;

    await expect(request("/documents/x")).resolves.toEqual({ id: "doc1" });
  });

  it("HTTP 非 2xx 时抛出包含状态码的错误", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "bad request" }), { status: 400 }),
    ) as unknown as typeof fetch;

    await expect(request("/documents/upload")).rejects.toThrow(/400/);
  });

  it("HTTP 500 时抛出包含状态码的错误", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "server error" }), { status: 500 }),
    ) as unknown as typeof fetch;

    await expect(request("/documents")).rejects.toThrow(/500/);
  });

  it("HTTP 422 detail 为数组时拼出可读错误", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ detail: [{ loc: ["body", "workspace_id"], msg: "Field required" }] }),
        { status: 422, statusText: "Unprocessable Entity" },
      ),
    ) as unknown as typeof fetch;

    await expect(request("/documents/upload")).rejects.toThrow(/workspace_id.*Field required/);
  });

  it("业务码非 200 时抛出包含 message 的错误", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ code: 4001, message: "文件不支持" }), { status: 200 }),
    ) as unknown as typeof fetch;

    await expect(request("/documents/upload")).rejects.toThrow(/文件不支持/);
  });

  it("透传 options（method / headers）", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ code: 200, data: {} }), { status: 200 }),
    );
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await request("/documents", { method: "GET", headers: { "X-Test": "1" } });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const callArgs = fetchMock.mock.calls[0];
    expect(callArgs?.[1]).toMatchObject({ method: "GET" });
  });
});

describe("apiClient.uploadFile", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("使用 POST 方法发送 FormData 并解包响应", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ code: 200, data: { id: "doc2" } }), { status: 200 }),
    );
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const formData = new FormData();
    formData.append("file", new File(["x"], "a.pdf"));

    await expect(uploadFile("/documents/upload", formData)).resolves.toEqual({ id: "doc2" });

    const callArgs = fetchMock.mock.calls[0];
    expect(callArgs?.[0]).toContain("/api/documents/upload");
    expect(callArgs?.[1]).toMatchObject({ method: "POST", body: formData });
  });
});

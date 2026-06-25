import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../../../lib/apiClient", () => ({ request: vi.fn() }));

import { request } from "../../../lib/apiClient";
import {
  listProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  activateProvider,
  getActiveProvider,
} from "./providerApi";
import type { ProviderPayload } from "../types";

describe("providerApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("listProviders 不传 purpose 时 GET /providers", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    await listProviders();
    expect(request).toHaveBeenCalledWith("/providers");
  });

  it("listProviders 传 purpose 时附加查询参数", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    await listProviders("chat");
    expect(request).toHaveBeenCalledWith("/providers?purpose=chat");
  });

  it("createProvider POST /providers 发送 JSON body", async () => {
    const payload: ProviderPayload = {
      name: "deepseek",
      api_mode: "openai-compat",
      api_key: "sk-x",
      api_host: "https://api.deepseek.com",
      model_id: "deepseek-chat",
      display_name: "DeepSeek",
      purpose: "chat",
    };
    (request as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "cfg-1" });
    const result = await createProvider(payload);
    expect(result).toEqual({ id: "cfg-1" });
    const [path, options] = (request as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/providers");
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body as string)).toEqual(payload);
  });

  it("updateProvider PATCH /providers/{id}", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "cfg-1" });
    await updateProvider("cfg-1", { display_name: "New" });
    const [path, options] = (request as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/providers/cfg-1");
    expect(options.method).toBe("PATCH");
  });

  it("deleteProvider DELETE /providers/{id}", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    const result = await deleteProvider("cfg-1");
    expect(result).toBe(true);
    expect(request).toHaveBeenCalledWith("/providers/cfg-1", { method: "DELETE" });
  });

  it("activateProvider POST /providers/{id}/activate", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "cfg-1" });
    await activateProvider("cfg-1");
    expect(request).toHaveBeenCalledWith("/providers/cfg-1/activate", { method: "POST" });
  });

  it("getActiveProvider GET /providers/active?purpose=", async () => {
    (request as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "cfg-1" });
    await getActiveProvider("embedding");
    expect(request).toHaveBeenCalledWith("/providers/active?purpose=embedding");
  });
});

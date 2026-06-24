import { describe, it, expect, vi, beforeEach } from "vitest";

// documentApi 是对 apiClient 的薄封装，这里 mock apiClient 验证调用契约。
vi.mock("../../../lib/apiClient", () => ({
  request: vi.fn(),
  uploadFile: vi.fn(),
}));

import { request, uploadFile } from "../../../lib/apiClient";
import { uploadDocument, getDocumentDetail, listDocuments } from "./documentApi";

describe("documentApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("uploadDocument", () => {
    it("构造 FormData（含 file 和 workspace_id）并 POST 到 /documents/upload", async () => {
      (uploadFile as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "doc1" });

      const file = new File(["content"], "lecture.pdf", { type: "application/pdf" });
      const result = await uploadDocument(file, "workspace_1");

      expect(result).toEqual({ id: "doc1" });
      expect(uploadFile).toHaveBeenCalledTimes(1);

      const [path, formData] = (uploadFile as ReturnType<typeof vi.fn>).mock.calls[0];
      expect(path).toBe("/documents/upload");
      expect(formData.get("file")).toBe(file);
      expect(formData.get("workspace_id")).toBe("workspace_1");
    });

    it("未传 workspace_id 时不附加该字段", async () => {
      (uploadFile as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "doc2" });

      const file = new File(["content"], "lecture.pdf");
      await uploadDocument(file);

      const formData = (uploadFile as ReturnType<typeof vi.fn>).mock.calls[0][1];
      expect(formData.get("file")).toBe(file);
      expect(formData.has("workspace_id")).toBe(false);
    });
  });

  describe("getDocumentDetail", () => {
    it("GET /documents/{id} 获取详情", async () => {
      const detail = { document: { id: "doc1" }, units: [] };
      (request as ReturnType<typeof vi.fn>).mockResolvedValue(detail);

      const result = await getDocumentDetail("doc1");

      expect(result).toEqual(detail);
      expect(request).toHaveBeenCalledWith("/documents/doc1");
    });
  });

  describe("listDocuments", () => {
    it("GET /documents 并附带 workspace_id 查询参数", async () => {
      (request as ReturnType<typeof vi.fn>).mockResolvedValue([{ id: "doc1" }]);

      const result = await listDocuments("workspace_1");

      expect(result).toEqual([{ id: "doc1" }]);
      expect(request).toHaveBeenCalledWith("/documents?workspace_id=workspace_1");
    });

    it("对 workspace_id 做 URL 编码", async () => {
      (request as ReturnType<typeof vi.fn>).mockResolvedValue([]);

      await listDocuments("cours & notes");

      expect(request).toHaveBeenCalledWith("/documents?workspace_id=cours%20%26%20notes");
    });
  });
});

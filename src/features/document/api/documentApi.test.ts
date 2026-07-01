import { afterEach, describe, expect, it, vi } from "vitest";
import {
  confirmOutlineCandidate,
  uploadDocument,
} from "./documentApi";

describe("documentApi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uploads a PDF through the real backend endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        code: 200,
        data: {
          document_id: "doc-1",
          filename: "cours.pdf",
          page_count: 2,
          status: "parsed",
          page_index: { document_id: "doc-1", page_count: 2, pages: [] },
          outline_candidates: [
            { id: "pdf_outline", source: "pdf_outline", status: "unavailable", sections: [] },
            { id: "llm_outline", source: "llm_outline", status: "available", sections: [] },
          ],
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await uploadDocument(
      new File(["pdf"], "cours.pdf", { type: "application/pdf" }),
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/documents/upload",
      expect.objectContaining({ method: "POST", body: expect.any(FormData) }),
    );
    expect(result.documentId).toBe("doc-1");
    expect(result.outlineCandidates).toHaveLength(2);
  });

  it("confirms an outline candidate and maps formal sections", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        code: 200,
        data: {
          sections: [
            {
              id: "sec-1",
              title: "Introduction",
              level: 1,
              order_index: 0,
              parent_section_id: null,
            },
          ],
          section_unit_links_status: "metadata_fallback",
          chunk_status: "created",
          embedding_status: "unavailable",
        },
      }),
    }));

    const result = await confirmOutlineCandidate("doc-1", {
      id: "pdf_outline",
      source: "pdf_outline",
      status: "available",
      sections: [],
    });

    expect(result.sections[0]).toMatchObject({
      id: "sec-1",
      title: "Introduction",
      index: "1",
    });
    expect(result.sectionUnitLinksStatus).toBe("metadata_fallback");
  });
});

import { beforeEach, describe, expect, it, vi } from "vitest";
import { request } from "../../../lib/apiClient";
import { buildSections, getSectionContent, getSectionTree } from "./sectionApi";

vi.mock("../../../lib/apiClient", () => ({
  request: vi.fn(),
}));

describe("sectionApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("buildSections posts to the document section build endpoint", async () => {
    vi.mocked(request).mockResolvedValueOnce([{ id: "s1", title: "第一章", level: 1 }]);

    const result = await buildSections("doc-1");

    expect(request).toHaveBeenCalledWith("/sections/documents/doc-1/build", { method: "POST" });
    expect(result).toEqual([{ id: "s1", title: "第一章", level: 1 }]);
  });

  it("getSectionTree maps page range metadata into frontend nodes", async () => {
    vi.mocked(request).mockResolvedValueOnce([
      {
        id: "s1",
        title: "第一章",
        level: 1,
        order_index: 0,
        start_page: 1,
        end_page: 3,
        children: [],
      },
    ]);

    const result = await getSectionTree("doc-1");

    expect(request).toHaveBeenCalledWith("/sections/documents/doc-1/tree");
    expect(result).toEqual([
      {
        id: "s1",
        title: "第一章",
        index: "1",
        expanded: true,
        startPage: 1,
        endPage: 3,
        children: [],
      },
    ]);
  });

  it("getSectionTree generates correct sibling indexes for nested nodes", async () => {
    vi.mocked(request).mockResolvedValueOnce([
      {
        id: "s1",
        title: "Epic 总览",
        level: 1,
        order_index: 6,
        start_page: null,
        end_page: null,
        children: [
          {
            id: "s2",
            title: "Epic 结构",
            level: 2,
            order_index: 7,
            start_page: null,
            end_page: null,
            children: [],
          },
          {
            id: "s3",
            title: "优先级总表",
            level: 2,
            order_index: 8,
            start_page: null,
            end_page: null,
            children: [],
          },
        ],
      },
      {
        id: "s4",
        title: "Epic 1: 文件上传与解析",
        level: 1,
        order_index: 9,
        start_page: null,
        end_page: null,
        children: [],
      },
      {
        id: "s5",
        title: "Epic 2: 本地数据模型",
        level: 1,
        order_index: 16,
        start_page: null,
        end_page: null,
        children: [],
      },
    ]);

    const result = await getSectionTree("doc-1");

    // 验证同级编号正确：不应该用 order_index+1，而是用同级索引
    expect(result[0].index).toBe("1");      // 第一个顶级节点
    expect(result[0].children[0].index).toBe("1.1");  // 第一个子节点
    expect(result[0].children[1].index).toBe("1.2");  // 第二个子节点
    expect(result[1].index).toBe("2");      // 第二个顶级节点
    expect(result[2].index).toBe("3");      // 第三个顶级节点
  });

  it("getSectionContent loads source units for one section", async () => {
    const payload = {
      anchor_unit_id: "u1",
      units: [
        { id: "u1", sequence_index: 0, page_number: 1, text_content: "Section source" },
      ],
    };
    vi.mocked(request).mockResolvedValueOnce(payload);

    const result = await getSectionContent("section-1");

    expect(request).toHaveBeenCalledWith("/sections/section-1/content");
    expect(result).toEqual(payload);
  });
});

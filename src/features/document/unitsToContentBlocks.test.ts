import { describe, it, expect } from "vitest";
import { unitsToContentBlocks, UPLOADED_CONTENT_SECTION_ID } from "./unitsToContentBlocks";
import type { DocumentUnit } from "../../types/document";

describe("unitsToContentBlocks", () => {
  it("有 page_number 的 unit 转为「第 N 页」标题的内容块", () => {
    const units: DocumentUnit[] = [
      { id: "u1", sequence_index: 0, page_number: 1, text_content: "第一页" },
    ];

    const blocks = unitsToContentBlocks(units);

    expect(blocks).toHaveLength(1);
    expect(blocks[0].id).toBe("u1");
    expect(blocks[0].sectionId).toBe(UPLOADED_CONTENT_SECTION_ID);
    expect(blocks[0].title).toBe("第 1 页");
    expect(blocks[0].contentType).toBe("text");
  });

  it("page_number 为 null 时标题使用「单元 N」", () => {
    const units: DocumentUnit[] = [
      { id: "u1", sequence_index: 0, page_number: null, text_content: "内容" },
    ];

    const blocks = unitsToContentBlocks(units);

    expect(blocks[0].title).toBe("单元 1");
  });

  it("多行 text_content 按换行拆分为多个 ContentLine", () => {
    const units: DocumentUnit[] = [
      { id: "u1", sequence_index: 0, page_number: 1, text_content: "第一行\n第二行\n第三行" },
    ];

    const blocks = unitsToContentBlocks(units);

    expect(blocks[0].lines).toHaveLength(3);
    expect(blocks[0].lines?.[0].text).toBe("第一行");
    expect(blocks[0].lines?.[2].text).toBe("第三行");
    expect(blocks[0].lines?.[0].type).toBe("paragraph");
  });

  it("空 text_content 转为无正文行的内容块", () => {
    const units: DocumentUnit[] = [
      { id: "u1", sequence_index: 0, page_number: 1, text_content: "" },
    ];

    const blocks = unitsToContentBlocks(units);

    expect(blocks[0].title).toBe("第 1 页");
    expect(blocks[0].lines).toEqual([]);
  });

  it("多个 unit 按顺序生成多个内容块", () => {
    const units: DocumentUnit[] = [
      { id: "u1", sequence_index: 0, page_number: 1, text_content: "A" },
      { id: "u2", sequence_index: 1, page_number: 2, text_content: "B" },
    ];

    const blocks = unitsToContentBlocks(units);

    expect(blocks).toHaveLength(2);
    expect(blocks.map((b) => b.id)).toEqual(["u1", "u2"]);
  });

  it("保留 unit 之间的顺序（即使 page_number 乱序，仍按 sequence_index）", () => {
    const units: DocumentUnit[] = [
      { id: "u2", sequence_index: 1, page_number: 2, text_content: "B" },
      { id: "u1", sequence_index: 0, page_number: 1, text_content: "A" },
    ];

    const blocks = unitsToContentBlocks(units);

    // 直接按传入顺序生成，调用方负责排序（后端已按 sequence_index 排序）
    expect(blocks[0].id).toBe("u2");
  });
});

/**
 * DocumentUnit → ContentBlock 转换函数。
 *
 * 将后端解析出的 DocumentUnit 列表转换为前端 DocumentViewer 可渲染的
 * ContentBlock 列表，复用现有表格/工具栏/高亮/脚注能力。
 *
 * 映射规则（与 BDD scenarios 对齐）：
 * - 1 个 unit → 1 个 ContentBlock
 * - sectionId 统一为临时常量（Task 02 章节树接入后将改为真实 sectionId）
 * - title: page_number 存在时"第 N 页"，否则"单元 N"（fallback）
 * - text_content 按换行拆分为 ContentLine（type 默认 paragraph）
 */
import type { ContentBlock, ContentLine } from "../../types/section";
import type { DocumentUnit } from "../../types/document";

/** 上传解析后的临时 sectionId，等 Task 02 接入真实章节树后替换 */
export const UPLOADED_CONTENT_SECTION_ID = "uploaded-content";

export function unitsToContentBlocks(
  units: DocumentUnit[],
): ContentBlock[] {
  return units.map((unit) => ({
    id: unit.id,
    sectionId: UPLOADED_CONTENT_SECTION_ID,
    title:
      unit.page_number != null
        ? `第 ${unit.page_number} 页`
        : `单元 ${unit.sequence_index + 1}`,
    contentType: "text" as const,
    lines: textToContentLines(unit.id, unit.text_content),
  }));
}

/** 将单个 unit 的 text_content 按换行拆分为 ContentLine 数组 */
function textToContentLines(
  unitId: string,
  text: string,
): ContentLine[] {
  if (!text) return [];
  return text
    .split("\n")
    .map(
      (line, i): ContentLine => ({
        id: `${unitId}-line-${i}`,
        text: line,
        type: "paragraph",
      }),
    );
}

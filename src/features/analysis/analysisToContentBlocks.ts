import type { SectionAnalysisResponse } from "../../types/analysis";
import type { ContentBlock, ContentLine } from "../../types/section";

function toParagraphLines(prefix: string, values: string[]): ContentLine[] {
  return values.map((value, index) => ({
    id: `${prefix}-${index}`,
    text: value,
    type: "paragraph",
  }));
}

export function analysisToContentBlocks(analysis: SectionAnalysisResponse): ContentBlock[] {
  const content = analysis.content_json;
  if (!content) return [];

  const sectionId = analysis.section_id;
  const blocks: ContentBlock[] = [];

  if (content.summary) {
    blocks.push({
      id: `${sectionId}-summary`,
      sectionId,
      title: "摘要",
      contentType: "text",
      lines: [
        { id: `${sectionId}-summary-line`, text: content.summary, type: "paragraph" },
      ],
    });
  }

  if (content.key_concepts.length > 0) {
    blocks.push({
      id: `${sectionId}-concepts`,
      sectionId,
      title: "核心概念",
      contentType: "text",
      lines: toParagraphLines(`${sectionId}-concept`, content.key_concepts),
    });
  }

  if (content.terms.length > 0) {
    blocks.push({
      id: `${sectionId}-terms`,
      sectionId,
      title: "中法术语",
      contentType: "text",
      lines: content.terms.map((term, index) => ({
        id: `${sectionId}-term-${index}`,
        text: `${term.fr} / ${term.zh}：${term.explanation}`,
        type: "paragraph",
      })),
    });
  }

  if (content.highlights.length > 0) {
    blocks.push({
      id: `${sectionId}-highlights`,
      sectionId,
      title: "重点提炼",
      contentType: "text",
      lines: toParagraphLines(`${sectionId}-highlight`, content.highlights),
    });
  }

  return blocks;
}

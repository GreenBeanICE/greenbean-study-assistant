import type { ReactNode } from "react";
import type { SourceCitation, SourcePage } from "../../../../types/section";

interface SourcePanelProps {
  sourcePages: SourcePage[];
  activeCitations: SourceCitation[];
}

function renderHighlightedPageText(page: SourcePage, citations: SourceCitation[]) {
  const pageCitations = citations
    .filter((citation) => citation.documentUnitId === page.documentUnitId)
    .sort((a, b) => a.startChar - b.startChar);

  if (pageCitations.length === 0) {
    return <span>{page.text}</span>;
  }

  const parts: ReactNode[] = [];
  let cursor = 0;
  pageCitations.forEach((citation) => {
    const start = Math.max(0, Math.min(citation.startChar, page.text.length));
    const end = Math.max(start, Math.min(citation.endChar, page.text.length));
    if (start > cursor) {
      parts.push(<span key={`${citation.id}-before`}>{page.text.slice(cursor, start)}</span>);
    }
    parts.push(
      <mark
        key={citation.id}
        data-source-highlight="true"
        className="rounded bg-yellow-200/80 px-0.5 text-neutral-900"
      >
        {page.text.slice(start, end) || citation.sourceText}
      </mark>,
    );
    cursor = end;
  });
  if (cursor < page.text.length) {
    parts.push(<span key="tail">{page.text.slice(cursor)}</span>);
  }
  return parts;
}

function SourcePanel({ sourcePages, activeCitations }: SourcePanelProps) {
  if (sourcePages.length === 0 || activeCitations.length === 0) {
    return (
      <div className="flex h-full flex-col bg-white/70">
        <div className="border-b border-black/5 px-4 py-3">
          <h2 className="text-sm font-semibold text-neutral-700">文字版 PDF 来源</h2>
        </div>
        <div className="flex flex-1 items-center justify-center px-6 text-center">
          <p className="text-sm text-neutral-500">选择解析文本后右键显示来源</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-white/70">
      <div className="border-b border-black/5 px-4 py-3">
        <h2 className="text-sm font-semibold text-neutral-700">文字版 PDF 来源</h2>
        <p className="mt-1 text-xs text-neutral-500">
          已高亮 {activeCitations.length} 处来源
        </p>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3">
        <div className="space-y-4">
          {sourcePages.map((page) => (
            <section key={page.documentUnitId} className="rounded-lg border border-black/10 bg-white p-3">
              <h3 className="mb-2 text-xs font-semibold text-neutral-500">
                第 {page.page ?? "未知"} 页
              </h3>
              <p className="whitespace-pre-wrap text-sm leading-7 text-neutral-700">
                {renderHighlightedPageText(page, activeCitations)}
              </p>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}

export default SourcePanel;

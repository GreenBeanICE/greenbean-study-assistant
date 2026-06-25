# 原文面板实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 DocumentViewer 中新增左右双栏布局，同时显示原文和解析内容，支持同步滚动和面板隐藏。

**Architecture:** 复用现有 getDocumentDetail 接口获取 DocumentUnit 数据，新增 RawTextPanel 组件展示原文，修改 DocumentViewer 支持双栏布局和同步滚动。

**Tech Stack:** React 19、TypeScript、Framer Motion、Vitest

---

## 文件结构

```
src/features/workspace/components/center/
├── DocumentViewer.tsx          (修改：双栏布局、同步滚动、面板隐藏)
├── DocumentViewer.test.tsx     (修改：补充双栏布局测试)
├── RawTextPanel.tsx            (新增：原文面板组件)
└── RawTextPanel.test.tsx       (新增：原文面板测试)

src/features/workspace/pages/
├── WorkspacePage.tsx           (修改：添加状态管理、传递新 props)
└── WorkspacePage.test.tsx      (修改：补充状态管理测试)

src/features/workspace/type.ts  (修改：扩展 DocumentViewerProps)
```

---

## Task 1: 扩展 DocumentViewerProps 类型

**Files:**
- Modify: `src/features/workspace/type.ts:77-91`

- [ ] **Step 1: 修改 DocumentViewerProps 接口**

```typescript
export interface DocumentViewerProps {
  contentBlocks: ContentBlock[];
  selectedSectionId: string | null;
  viewerStatus?: ViewerStatus;
  pendingFileName?: string;
  errorMessage?: string | null;
  footnotes: FootnoteReference[];
  expandedFootnoteId: string | null;
  showSelectionMenu: boolean;
  selectionMenuPos: { x: number; y: number } | null;
  onUpdateLineText: (blockId: string, lineId: string, text: string) => void;
  onToggleFootnote: (footnoteId: string) => void;
  onShowSelectionMenu: (show: boolean, pos?: { x: number; y: number }) => void;
  onQuoteSelection: () => void;
  // 新增：原文面板相关 props
  units?: import("../../types/document").DocumentUnit[];
  showRawPanel?: boolean;
  showParsedPanel?: boolean;
  onToggleRawPanel?: () => void;
  onToggleParsedPanel?: () => void;
}
```

- [ ] **Step 2: 运行类型检查**

Run: `npm run typecheck`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/features/workspace/type.ts
git commit -m "feat: extend DocumentViewerProps with raw panel props"
```

---

## Task 2: 创建 RawTextPanel 组件

**Files:**
- Create: `src/features/workspace/components/center/RawTextPanel.tsx`
- Create: `src/features/workspace/components/center/RawTextPanel.test.tsx`

- [ ] **Step 1: 写失败测试**

```tsx
// RawTextPanel.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import RawTextPanel from "./RawTextPanel";
import type { DocumentUnit } from "../../../../types/document";

const mockUnits: DocumentUnit[] = [
  { id: "u1", sequence_index: 0, page_number: 1, text_content: "第一页内容" },
  { id: "u2", sequence_index: 1, page_number: 2, text_content: "第二页内容" },
];

describe("RawTextPanel", () => {
  it("renders empty state when units is empty", () => {
    render(<RawTextPanel units={[]} />);
    expect(screen.getByText("暂无原文数据")).toBeDefined();
  });

  it("renders units with page numbers", () => {
    render(<RawTextPanel units={mockUnits} />);
    expect(screen.getByText("第 1 页")).toBeDefined();
    expect(screen.getByText("第一页内容")).toBeDefined();
    expect(screen.getByText("第 2 页")).toBeDefined();
    expect(screen.getByText("第二页内容")).toBeDefined();
  });

  it("highlights selected unit", () => {
    render(<RawTextPanel units={mockUnits} selectedUnitId="u1" />);
    const selectedUnit = screen.getByText("第一页内容").closest("[data-unit-id]");
    expect(selectedUnit?.getAttribute("data-unit-id")).toBe("u1");
  });

  it("calls onUnitClick when unit is clicked", () => {
    const onUnitClick = vi.fn();
    render(<RawTextPanel units={mockUnits} onUnitClick={onUnitClick} />);
    fireEvent.click(screen.getByText("第一页内容"));
    expect(onUnitClick).toHaveBeenCalledWith("u1");
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `npm run test:frontend -- RawTextPanel`
Expected: FAIL with "Cannot find module"

- [ ] **Step 3: 实现 RawTextPanel 组件**

```tsx
// RawTextPanel.tsx
import type { DocumentUnit } from "../../../../types/document";

interface RawTextPanelProps {
  units: DocumentUnit[];
  selectedUnitId?: string | null;
  onUnitClick?: (unitId: string) => void;
}

function RawTextPanel({ units, selectedUnitId, onUnitClick }: RawTextPanelProps) {
  if (units.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-4">
        <div className="w-12 h-12 rounded-2xl bg-black/5 flex items-center justify-center mb-3">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" className="text-neutral-400">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
          </svg>
        </div>
        <p className="text-sm text-neutral-400">暂无原文数据</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto px-4 py-4 scrollbar-hide" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
      {units.map((unit) => {
        const isSelected = selectedUnitId === unit.id;
        const pageLabel = unit.page_number != null ? `第 ${unit.page_number} 页` : `单元 ${unit.sequence_index + 1}`;

        return (
          <div
            key={unit.id}
            data-unit-id={unit.id}
            onClick={() => onUnitClick?.(unit.id)}
            className={`mb-4 p-3 rounded-lg cursor-pointer transition-colors ${
              isSelected
                ? "bg-blue-50 border border-blue-200"
                : "hover:bg-black/[0.02]"
            }`}
          >
            <div className="text-xs font-medium text-neutral-400 mb-2">{pageLabel}</div>
            <div className="text-sm text-neutral-700 leading-relaxed whitespace-pre-wrap">
              {unit.text_content || <span className="text-neutral-300 italic">（空内容）</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default RawTextPanel;
```

- [ ] **Step 4: 运行测试验证通过**

Run: `npm run test:frontend -- RawTextPanel`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/features/workspace/components/center/RawTextPanel.tsx src/features/workspace/components/center/RawTextPanel.test.tsx
git commit -m "feat: add RawTextPanel component for original text display"
```

---

## Task 3: 修改 DocumentViewer 支持双栏布局

**Files:**
- Modify: `src/features/workspace/components/center/DocumentViewer.tsx:311-384`
- Modify: `src/features/workspace/components/center/DocumentViewer.test.tsx`

- [ ] **Step 1: 写失败测试**

```tsx
// DocumentViewer.test.tsx 补充测试
it("renders both panels when showRawPanel and showParsedPanel are true", () => {
  render(
    <DocumentViewer
      contentBlocks={mockContentBlocks}
      units={mockUnits}
      showRawPanel={true}
      showParsedPanel={true}
      // ... other required props
    />
  );
  expect(screen.getByText("原文")).toBeDefined();
  expect(screen.getByText("解析")).toBeDefined();
  expect(screen.getByText("第一页内容")).toBeDefined(); // 原文
});

it("hides raw panel when showRawPanel is false", () => {
  render(
    <DocumentViewer
      contentBlocks={mockContentBlocks}
      units={mockUnits}
      showRawPanel={false}
      showParsedPanel={true}
      // ... other required props
    />
  );
  expect(screen.queryByText("第一页内容")).toBeNull(); // 原文不显示
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `npm run test:frontend -- DocumentViewer`
Expected: FAIL

- [ ] **Step 3: 修改 DocumentViewer 实现双栏布局**

修改 `DocumentViewer.tsx` 的 return 部分：

```tsx
return (
  <div className="flex flex-col h-full">
    {/* 顶部栏 */}
    <div className="flex flex-wrap items-center px-4 py-2 border-b border-black/5 bg-white/50 gap-x-1">
      <h2 className="text-sm font-semibold text-neutral-700 tracking-tight whitespace-nowrap flex-shrink-0">文档解析</h2>
      <div className="flex items-center gap-1.5 flex-shrink-0 ml-auto">
        {/* 新增：原文/解析切换按钮 */}
        {units && units.length > 0 && (
          <>
            <button onClick={onToggleRawPanel}
              className={`cursor-pointer px-2 py-1 text-xs rounded transition ${showRawPanel ? 'bg-blue-100 text-blue-700' : 'text-neutral-400 hover:bg-black/10'}`}>
              原文
            </button>
            <button onClick={onToggleParsedPanel}
              className={`cursor-pointer px-2 py-1 text-xs rounded transition ${showParsedPanel ? 'bg-blue-100 text-blue-700' : 'text-neutral-400 hover:bg-black/10'}`}>
              解析
            </button>
          </>
        )}
        <button onClick={handleDownload}
          className="cursor-pointer w-7 h-7 rounded-md flex items-center justify-center hover:bg-black/10 text-neutral-400 transition"
          title="下载">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
        </button>
        <button onClick={handleShare}
          className="cursor-pointer w-7 h-7 rounded-md flex items-center justify-center hover:bg-black/10 text-neutral-400 transition"
          title="分享">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" /></svg>
        </button>
      </div>
    </div>

    {/* 工具栏 */}
    <DocumentToolbar selectedLineId={hasSelection ? "selected" : null} />

    {/* 双栏内容区域 */}
    <div className="flex-1 flex overflow-hidden min-h-0">
      {/* 原文面板 */}
      {showRawPanel && units && units.length > 0 && (
        <>
          <div className="w-1/2 overflow-hidden" ref={rawPanelRef} onScroll={handleRawScroll}>
            <RawTextPanel units={units} selectedUnitId={selectedSectionId} onUnitClick={onUnitClick} />
          </div>
          <div className="w-px bg-black/5 flex-shrink-0" />
        </>
      )}

      {/* 解析面板 */}
      {showParsedPanel && (
        <div
          ref={parsedPanelRef}
          onScroll={handleParsedScroll}
          className={`flex-1 overflow-y-auto overflow-x-auto px-6 md:px-10 py-4 scrollbar-hide ${showRawPanel && units && units.length > 0 ? 'w-1/2' : 'w-full'}`}
          style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
        >
          {/* 现有的解析内容渲染逻辑 */}
          {showEmptyState ? (
            <div className="inline-block pt-16 pl-6">
              <div className="w-16 h-16 rounded-2xl bg-black/5 flex items-center justify-center mb-4">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" className="text-neutral-400">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
                </svg>
              </div>
              <p className="text-sm text-neutral-500 font-medium">
                {emptyStateCopy.title}
              </p>
              <p className="text-xs text-neutral-400 mt-1">
                {emptyStateCopy.subtitle}
              </p>
            </div>
          ) : (
            <div className="min-w-max" style={{ minWidth: "max-content" }}>
              <div className="max-w-3xl mx-auto">
                {filteredBlocks.map((block, idx) => (
                  <div key={block.id}>
                    {idx > 0 && <hr className="my-4 border-black/5" />}
                    <h3 className="text-base font-semibold text-neutral-800 mb-3 tracking-tight">
                      <EditableText text={block.title} onBlur={(val) => {
                        onUpdateLineText(block.id, `title-${block.id}`, val);
                      }} />
                    </h3>
                    <BlockContent block={block} onViewFootnote={handleViewFootnote} onLineHtmlChange={handleLineHtmlChange} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>

    <AnimatePresence>
      {expandedFootnote && <FootnotePanel footnote={expandedFootnote} onClose={() => onToggleFootnote(expandedFootnote.id)} />}
    </AnimatePresence>

    {showSelectionMenuVisible && (
      <SelectionMenu
        pos={selectionMenuPos!}
        onQuote={onQuoteSelection}
        onClose={() => onShowSelectionMenu(false)}
      />
    )}
  </div>
);
```

- [ ] **Step 4: 添加同步滚动逻辑和新 props 解构**

在组件顶部添加：

```tsx
const {
  contentBlocks, selectedSectionId, viewerStatus, pendingFileName, errorMessage,
  footnotes, expandedFootnoteId, showSelectionMenu, selectionMenuPos,
  onUpdateLineText, onToggleFootnote, onShowSelectionMenu, onQuoteSelection,
  units, showRawPanel = true, showParsedPanel = true, onToggleRawPanel, onToggleParsedPanel
} = props;

const rawPanelRef = useRef<HTMLDivElement>(null);
const parsedPanelRef = useRef<HTMLDivElement>(null);
const isSyncingRef = useRef(false);

const handleRawScroll = useCallback(() => {
  if (isSyncingRef.current || !parsedPanelRef.current || !rawPanelRef.current) return;
  isSyncingRef.current = true;
  const ratio = rawPanelRef.current.scrollTop / (rawPanelRef.current.scrollHeight - rawPanelRef.current.clientHeight);
  parsedPanelRef.current.scrollTop = ratio * (parsedPanelRef.current.scrollHeight - parsedPanelRef.current.clientHeight);
  requestAnimationFrame(() => { isSyncingRef.current = false; });
}, []);

const handleParsedScroll = useCallback(() => {
  if (isSyncingRef.current || !parsedPanelRef.current || !rawPanelRef.current) return;
  isSyncingRef.current = true;
  const ratio = parsedPanelRef.current.scrollTop / (parsedPanelRef.current.scrollHeight - parsedPanelRef.current.clientHeight);
  rawPanelRef.current.scrollTop = ratio * (rawPanelRef.current.scrollHeight - rawPanelRef.current.clientHeight);
  requestAnimationFrame(() => { isSyncingRef.current = false; });
}, []);

const onUnitClick = useCallback((unitId: string) => {
  // 点击原文单元时，可以触发选中或滚动到对应的解析内容
}, []);
```

- [ ] **Step 5: 运行测试验证通过**

Run: `npm run test:frontend -- DocumentViewer`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/features/workspace/components/center/DocumentViewer.tsx src/features/workspace/components/center/DocumentViewer.test.tsx
git commit -m "feat: add dual-panel layout with sync scroll to DocumentViewer"
```

---

## Task 4: 修改 WorkspacePage 添加状态管理

**Files:**
- Modify: `src/features/workspace/pages/WorkspacePage.tsx:82-84, 217-262, 174-204`
- Modify: `src/features/workspace/pages/WorkspacePage.test.tsx`

- [ ] **Step 1: 写失败测试**

```tsx
// WorkspacePage.test.tsx 补充测试
it("caches document units after upload", async () => {
  // ... upload file
  // 验证 documentUnitsByFileId 有数据
});

it("loads units when selecting previously uploaded file", async () => {
  // ... upload file, select another file, then select first file
  // 验证 units 被正确加载
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `npm run test:frontend -- WorkspacePage`
Expected: FAIL

- [ ] **Step 3: 添加新状态变量**

```tsx
const [showRawPanel, setShowRawPanel] = useState(true);
const [showParsedPanel, setShowParsedPanel] = useState(true);
const [documentUnitsByFileId, setDocumentUnitsByFileId] = useState<Record<string, DocumentUnit[]>>({});
```

- [ ] **Step 4: 修改 handleUpload 缓存 units**

```tsx
const detail = await getDocumentDetail(uploadResult.id);
const blocks = unitsToContentBlocks(detail.units);

// 新增：缓存原始单元数据
setDocumentUnitsByFileId((prev) => ({
  ...prev,
  [fileId]: detail.units,
}));
```

- [ ] **Step 5: 修改 applyFileContent 加载 units**

```tsx
const blocks = documentBlocksByFileId[fileId] ?? [];
const sections = documentSectionsByFileId[fileId] ?? [];
const units = documentUnitsByFileId[fileId] ?? [];
```

- [ ] **Step 6: 传递新 props 给 DocumentViewer**

```tsx
<DocumentViewer
  contentBlocks={state.contentBlocks}
  units={documentUnitsByFileId[selectedFileId] ?? []}
  showRawPanel={showRawPanel}
  showParsedPanel={showParsedPanel}
  onToggleRawPanel={() => setShowRawPanel(!showRawPanel)}
  onToggleParsedPanel={() => setShowParsedPanel(!showParsedPanel)}
  // ... 其他现有 props
/>
```

- [ ] **Step 7: 运行测试验证通过**

Run: `npm run test:frontend -- WorkspacePage`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/features/workspace/pages/WorkspacePage.tsx src/features/workspace/pages/WorkspacePage.test.tsx
git commit -m "feat: add panel state management and units caching to WorkspacePage"
```

---

## Task 5: 运行全量测试并修复问题

**Files:**
- 无新增文件，修复可能的类型或测试问题

- [ ] **Step 1: 运行类型检查**

Run: `npm run typecheck`
Expected: PASS

- [ ] **Step 2: 运行全量前端测试**

Run: `npm run test:frontend`
Expected: All tests PASS

- [ ] **Step 3: 修复任何失败的测试**

- [ ] **Step 4: Final Commit**

```bash
git add -A
git commit -m "feat: complete raw text panel implementation"
```

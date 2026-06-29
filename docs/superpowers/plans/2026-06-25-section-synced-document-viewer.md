# Section Synced Document Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make PageIndex section selection drive the original text pane and parsed pane separately, without using original `DocumentUnit` text as fake parsed content.

**Architecture:** Reuse the existing backend section content endpoint. Add a frontend API wrapper, keep source units separate from parsed content blocks in `WorkspacePage`, and make `DocumentViewer` show a parsed empty state when no parsed block exists for the selected section.

**Tech Stack:** React 19, TypeScript, Vitest, Testing Library, existing `/api/sections` client wrapper, FastAPI backend contract already present.

---

## File Map

- Modify: `src/features/section/api/sectionApi.ts`
  - Add `getSectionContent(sectionId)` wrapper for `GET /api/sections/{sectionId}/content`.
- Create: `src/features/section/api/sectionApi.test.ts`
  - Verify section build, tree, and content API wrapper contracts.
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`
  - Stop converting `DocumentUnit` into parsed blocks on upload.
  - Store full source units separately from visible selected-section units.
  - Load section content when selecting a section.
  - Default to the first section after upload if a section tree exists.
- Modify: `src/features/workspace/components/center/DocumentViewer.tsx`
  - Keep original pane driven by `units`.
  - Show a parsed empty state when ready and selected section has no parsed blocks.
- Modify: `src/features/workspace/pages/WorkspacePage.test.tsx`
  - Mock section API and add regression coverage for section selection and empty parsed pane.
- Modify: `src/features/workspace/components/center/DocumentViewer.test.tsx`
  - Add direct coverage for parsed empty state with selected section and no parsed content.

## Task 1: Add Section Content API Wrapper

**Files:**
- Modify: `src/features/section/api/sectionApi.ts`
- Create: `src/features/section/api/sectionApi.test.ts`

- [ ] **Step 1: Write the failing API wrapper test**

Add `src/features/section/api/sectionApi.test.ts`:

```ts
import { describe, expect, it, vi, beforeEach } from "vitest";
import { buildSections, getSectionContent, getSectionTree } from "./sectionApi";
import { request } from "../../../lib/apiClient";

vi.mock("../../../lib/apiClient", () => ({
  request: vi.fn(),
}));

describe("sectionApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("buildSections posts to the document section build endpoint", async () => {
    vi.mocked(request).mockResolvedValueOnce([{ id: "s1", title: "Page 1", level: 1 }]);

    const result = await buildSections("doc-1");

    expect(request).toHaveBeenCalledWith("/sections/documents/doc-1/build");
    expect(result).toEqual([{ id: "s1", title: "Page 1", level: 1 }]);
  });

  it("getSectionTree maps backend nodes to frontend section nodes", async () => {
    vi.mocked(request).mockResolvedValueOnce([
      { id: "s1", title: "Root", level: 1, order_index: 0, children: [] },
    ]);

    const result = await getSectionTree("doc-1");

    expect(request).toHaveBeenCalledWith("/sections/documents/doc-1/tree");
    expect(result).toEqual([{ id: "s1", title: "Root", index: "1", expanded: true, children: [] }]);
  });

  it("getSectionContent loads source units for one section", async () => {
    const units = [
      { id: "u1", sequence_index: 0, page_number: 1, text_content: "Section source" },
    ];
    vi.mocked(request).mockResolvedValueOnce(units);

    const result = await getSectionContent("section-1");

    expect(request).toHaveBeenCalledWith("/sections/section-1/content");
    expect(result).toEqual(units);
  });
});
```

- [ ] **Step 2: Run the API wrapper test and verify Red**

Run: `rtk npm test -- src/features/section/api/sectionApi.test.ts --runInBand`

Expected: FAIL because `getSectionContent` is not exported from `sectionApi.ts`.

- [ ] **Step 3: Implement the minimal API wrapper**

Update `src/features/section/api/sectionApi.ts`:

```ts
import { request } from "../../../lib/apiClient";
import type { SectionNode } from "../../../types/section";
import type { DocumentUnit } from "../../../types/document";
```

Add this function after `getSectionTree`:

```ts
export async function getSectionContent(
  sectionId: string,
): Promise<DocumentUnit[]> {
  return request<DocumentUnit[]>(`/sections/${sectionId}/content`);
}
```

- [ ] **Step 4: Run the API wrapper test and verify Green**

Run: `rtk npm test -- src/features/section/api/sectionApi.test.ts --runInBand`

Expected: PASS.

## Task 2: Make DocumentViewer Show Parsed Empty State

**Files:**
- Modify: `src/features/workspace/components/center/DocumentViewer.tsx`
- Modify: `src/features/workspace/components/center/DocumentViewer.test.tsx`

- [ ] **Step 1: Write the failing DocumentViewer test**

Add this test inside `describe("DocumentViewer", () => { ... })` in `src/features/workspace/components/center/DocumentViewer.test.tsx`:

```tsx
  it("选择章节且没有解析块时显示该章节暂无解析内容", () => {
    render(
      <DocumentViewer
        {...defaultProps}
        contentBlocks={[]}
        selectedSectionId="ch1-1"
        viewerStatus="ready"
        units={[{ id: "u1", sequence_index: 0, page_number: 1, text_content: "原文内容" }]}
      />,
    );

    expect(screen.getByText("该章节暂无解析内容")).toBeDefined();
    expect(screen.queryByText("原文内容")).toBeDefined();
  });
```

- [ ] **Step 2: Run the DocumentViewer test and verify Red**

Run: `rtk npm test -- src/features/workspace/components/center/DocumentViewer.test.tsx --runInBand`

Expected: FAIL because the viewer currently uses the generic empty copy instead of `该章节暂无解析内容`.

- [ ] **Step 3: Implement parsed empty copy**

Update `src/features/workspace/components/center/DocumentViewer.tsx` around the empty state calculation:

```ts
  const hasSelectedSection = Boolean(selectedSectionId);
  const hasParsedBlocks = filteredBlocks.length > 0;
  const effectiveViewerStatus = viewerStatus === "idle" && hasSelectedSection && hasParsedBlocks
    ? "ready"
    : viewerStatus;
  const showEmptyState = effectiveViewerStatus !== "ready" || !hasSelectedSection || !hasParsedBlocks;
```

Update `emptyStateCopy` before the final default return:

```ts
    if (effectiveViewerStatus === "ready" && selectedSectionId && filteredBlocks.length === 0) {
      return {
        title: "该章节暂无解析内容",
        subtitle: "原文已加载，解析结果需要单独生成",
      };
    }
```

- [ ] **Step 4: Run the DocumentViewer test and verify Green**

Run: `rtk npm test -- src/features/workspace/components/center/DocumentViewer.test.tsx --runInBand`

Expected: PASS.

## Task 3: Stop Creating Fake Parsed Blocks on Upload

**Files:**
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`
- Modify: `src/features/workspace/pages/WorkspacePage.test.tsx`

- [ ] **Step 1: Mock section API in WorkspacePage tests**

Update imports in `src/features/workspace/pages/WorkspacePage.test.tsx`:

```ts
import { buildSections, getSectionContent, getSectionTree } from "../../section/api/sectionApi";
```

Add this mock after the existing document API mock:

```ts
vi.mock("../../section/api/sectionApi", () => ({
  buildSections: vi.fn(),
  getSectionTree: vi.fn(),
  getSectionContent: vi.fn(),
}));
```

Update `beforeEach`:

```ts
    (buildSections as Mock).mockResolvedValue([]);
    (getSectionTree as Mock).mockResolvedValue([]);
    (getSectionContent as Mock).mockResolvedValue([]);
```

- [ ] **Step 2: Update existing upload success expectation to source text only**

Replace the assertions in `上传 PDF 成功后展示解析出的分页文本` with:

```ts
    expect(await screen.findByText("第一页内容", {}, { timeout: 2000 })).toBeDefined();
    expect(screen.getByText("第二页内容")).toBeDefined();
    expect(screen.getByText("该章节暂无解析内容")).toBeDefined();
```

- [ ] **Step 3: Add failing regression test for section content selection**

Add this test in `WorkspacePage.test.tsx` near upload tests:

```tsx
  it("选择章节后加载该章节原文且解析面板保持空解析状态", async () => {
    (uploadDocument as Mock).mockResolvedValue({ id: "doc1" });
    (getDocumentDetail as Mock).mockResolvedValue({
      document: { id: "doc1" },
      units: [
        { id: "u1", sequence_index: 0, page_number: 1, text_content: "第一页全文" },
        { id: "u2", sequence_index: 1, page_number: 2, text_content: "第二页全文" },
      ],
    });
    (getSectionTree as Mock).mockResolvedValue([
      { id: "s1", title: "第一节", index: "1", expanded: true, children: [] },
      { id: "s2", title: "第二节", index: "2", expanded: true, children: [] },
    ]);
    (getSectionContent as Mock)
      .mockResolvedValueOnce([{ id: "u1", sequence_index: 0, page_number: 1, text_content: "第一节原文" }])
      .mockResolvedValueOnce([{ id: "u2", sequence_index: 1, page_number: 2, text_content: "第二节原文" }]);

    render(<WorkspacePage />);
    await uploadPdf("lecture.pdf");

    expect(await screen.findByText("第一节原文")).toBeDefined();
    expect(screen.queryByText("第二节原文")).toBeNull();
    expect(screen.getByText("该章节暂无解析内容")).toBeDefined();

    fireEvent.click(screen.getByText((content) => content.includes("第二节")));

    expect(await screen.findByText("第二节原文")).toBeDefined();
    expect(screen.queryByText("第一节原文")).toBeNull();
    expect(getSectionContent).toHaveBeenLastCalledWith("s2");
  });
```

- [ ] **Step 4: Run WorkspacePage tests and verify Red**

Run: `rtk npm test -- src/features/workspace/pages/WorkspacePage.test.tsx --runInBand`

Expected: FAIL because upload still creates parsed blocks from units and section selection does not call `getSectionContent`.

- [ ] **Step 5: Implement workspace state separation and section loading**

Update import in `src/features/workspace/pages/WorkspacePage.tsx`:

```ts
import { buildSections, getSectionContent, getSectionTree } from "../../section/api/sectionApi";
```

Remove this import because fake parsed conversion is no longer used:

```ts
import { unitsToContentBlocks, UPLOADED_CONTENT_SECTION_ID } from "../../document/unitsToContentBlocks";
```

Add state after `documentUnitsByFileId`:

```ts
  const [visibleUnitsByFileId, setVisibleUnitsByFileId] = useState<Record<string, DocumentUnit[]>>({});
```

Update `applyFileContent` so it uses visible units and does not auto-select `UPLOADED_CONTENT_SECTION_ID`:

```ts
    const blocks = documentBlocksByFileId[fileId] ?? [];
    const sections = documentSectionsByFileId[fileId] ?? [];
    const visibleUnits = visibleUnitsByFileId[fileId] ?? documentUnitsByFileId[fileId] ?? [];
    setViewerStatus(selectedFile?.viewerStatus ?? "ready");
    dispatch({ type: "SET_LANG_DATA", sections, contentBlocks: blocks });

    if (sections.length > 0) {
      dispatch({ type: "SELECT_SECTION", sectionId: sections[0].id });
      return;
    }

    if (visibleUnits.length > 0) {
      setViewerStatus("ready");
    }
    dispatch({ type: "SELECT_SECTION", sectionId: null });
```

Include `visibleUnitsByFileId` and `documentUnitsByFileId` in the `applyFileContent` dependency array.

Add a helper before `handleFileSelect`:

```ts
  const loadSectionContent = useCallback(async (fileId: string, sectionId: string) => {
    const units = await getSectionContent(sectionId);
    setVisibleUnitsByFileId((prev) => ({ ...prev, [fileId]: units }));
    setViewerStatus("ready");
    return units;
  }, []);
```

Update `handleSectionSelect`:

```ts
  const handleSectionSelect = useCallback((id: string) => {
    selectSection(id);
    if (selectedFileId) {
      loadSectionContent(selectedFileId, id).catch((err: unknown) => {
        setVisibleUnitsByFileId((prev) => ({ ...prev, [selectedFileId]: [] }));
        setUploadError(err instanceof Error ? err.message : "章节原文加载失败");
      });
    }
    setTimeout(() => {
      const el = document.getElementById(`block-${id}`);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  }, [loadSectionContent, selectSection, selectedFileId]);
```

In `handleUpload`, replace the fake block creation:

```ts
      const detail = await getDocumentDetail(uploadResult.id);
      const blocks: ContentBlock[] = [];
```

After section tree loading, choose initial visible units:

```ts
      let visibleUnits = detail.units;
      let initialSectionId: string | null = null;
      if (sections.length > 0) {
        initialSectionId = sections[0].id;
        try {
          visibleUnits = await getSectionContent(initialSectionId);
        } catch {
          visibleUnits = [];
        }
      }
```

Store visible units:

```ts
      setVisibleUnitsByFileId((prev) => ({
        ...prev,
        [fileId]: visibleUnits,
      }));
```

Replace the post-upload selection/status block:

```ts
      dispatch({ type: "SET_LANG_DATA", sections, contentBlocks: blocks });
      dispatch({ type: "SELECT_SECTION", sectionId: initialSectionId });
      setViewerStatus(detail.units.length > 0 || sections.length > 0 ? "ready" : "empty");
```

Update file viewerStatus:

```ts
          viewerStatus: detail.units.length > 0 || sections.length > 0 ? "ready" : "empty",
```

Update `DocumentViewer` props at the bottom:

```tsx
            units={selectedFileId ? (visibleUnitsByFileId[selectedFileId] ?? documentUnitsByFileId[selectedFileId]) : undefined}
```

- [ ] **Step 6: Run WorkspacePage tests and verify Green**

Run: `rtk npm test -- src/features/workspace/pages/WorkspacePage.test.tsx --runInBand`

Expected: PASS.

## Task 4: Focused Regression Run

**Files:**
- No code changes unless tests reveal a defect.

- [ ] **Step 1: Run all affected frontend tests**

Run: `rtk npm test -- src/features/section/api/sectionApi.test.ts src/features/workspace/components/center/DocumentViewer.test.tsx src/features/workspace/pages/WorkspacePage.test.tsx --runInBand`

Expected: PASS.

- [ ] **Step 2: Run broader frontend tests if focused tests pass**

Run: `rtk npm run test:frontend -- --runInBand`

Expected: PASS.

- [ ] **Step 3: Inspect concise git diff**

Run: `rtk git diff --stat`

Expected: only the spec, plan, API wrapper, viewer, workspace page, and related tests changed.

## Self-Review

- Spec coverage: Tasks cover section content API wrapper, source/parsed separation, selected section source loading, parsed empty state, and regression tests.
- Placeholder scan: No TODO/TBD placeholders are used.
- Type consistency: `DocumentUnit`, `SectionNode`, `ContentBlock`, `getSectionContent`, `selectedSectionId`, and `viewerStatus` names match existing code and new task definitions.

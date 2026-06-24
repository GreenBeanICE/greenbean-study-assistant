# Upload Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复前端上传联调在多文件、失败回退、空解析结果和 API 契约处理上的行为问题，保证“上传哪个文件，就看到哪个文件的内容”。

**Architecture:** 保留现有 `WorkspacePage` + `DocumentViewer` 结构，不做大重构。通过给 `FileItem` 增加后端文档映射和查看器状态，在页面层维护“已上传文件 -> 解析内容缓存”的最小状态；同时收紧 `apiClient` 和 `documentApi` 的类型与错误处理，补上对应单测。

**Tech Stack:** React 19, TypeScript, Vite 7, Vitest, Testing Library, FastAPI response contract

---

## File Map

- Modify: `src/features/workspace/type.ts`
  - 给 `FileItem` 增加后端文档映射与查看器状态字段。
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`
  - 在页面层维护按文件缓存的解析结果，修复选择文件/上传成功/上传失败/空结果时的状态流转。
- Modify: `src/features/workspace/components/center/DocumentViewer.tsx`
  - 显式渲染 `idle` / `parsing` / `empty` / `error` / `ready` 五种查看器状态，避免旧内容残留。
- Modify: `src/features/document/api/documentApi.ts`
  - 修正文档列表返回类型和查询参数编码。
- Modify: `src/types/document.ts`
  - 与后端 `DocumentListItem` / `DocumentDetailResponse` 对齐，补 `workspace_id`、`created_at`。
- Modify: `src/lib/apiClient.ts`
  - 兼容 FastAPI `detail` 为字符串、数组、对象三种错误结构。
- Modify: `src/features/workspace/pages/WorkspacePage.test.tsx`
  - 补连续上传、重新选择文件、失败清理、空 `units` 展示测试。
- Modify: `src/lib/apiClient.test.ts`
  - 补 422 数组 `detail` 的错误解包测试。
- Modify: `src/features/document/api/documentApi.test.ts`
  - 补 `workspace_id` URL 编码和列表返回类型契约测试。

### Task 1: 修复文件与解析结果的一一对应

**Files:**
- Modify: `src/features/workspace/type.ts`
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`
- Test: `src/features/workspace/pages/WorkspacePage.test.tsx`

- [ ] **Step 1: 写失败测试，覆盖“连续上传后切回旧文件仍应显示旧内容”**

```tsx
it("连续上传两份文档后，重新选择旧文件时显示该文件自己的解析内容", async () => {
  (uploadDocument as Mock)
    .mockResolvedValueOnce({ id: "doc-a" })
    .mockResolvedValueOnce({ id: "doc-b" });

  (getDocumentDetail as Mock)
    .mockResolvedValueOnce({
      document: { id: "doc-a", title: "A" },
      units: [{ id: "ua-1", sequence_index: 0, page_number: 1, text_content: "A 的第一页" }],
    })
    .mockResolvedValueOnce({
      document: { id: "doc-b", title: "B" },
      units: [{ id: "ub-1", sequence_index: 0, page_number: 1, text_content: "B 的第一页" }],
    });

  render(<WorkspacePage />);

  await uploadPdf("a.pdf");
  expect(await screen.findByText("A 的第一页")).toBeDefined();

  await uploadPdf("b.pdf");
  expect(await screen.findByText("B 的第一页")).toBeDefined();

  fireEvent.click(screen.getByText("a.pdf"));
  expect(await screen.findByText("A 的第一页")).toBeDefined();
  expect(screen.queryByText("B 的第一页")).toBeNull();
});
```

- [ ] **Step 2: 运行单测确认当前实现失败**

Run: `rtk npm run test:frontend -- WorkspacePage.test.tsx`

Expected: FAIL，表现为切回 `a.pdf` 后仍显示 `B 的第一页`，或中央区域没有正确切换。

- [ ] **Step 3: 给 `FileItem` 增加后端文档映射与查看器状态字段**

```ts
export type ViewerStatus = "idle" | "parsing" | "ready" | "empty" | "error";

export interface FileItem {
  id: string;
  name: string;
  type: FileType;
  category: string;
  size: string;
  date: string;
  status: FileStatus;
  documentId?: string;
  viewerStatus?: ViewerStatus;
}
```

- [ ] **Step 4: 在 `WorkspacePage` 中按文件缓存解析结果，并在选中文件时恢复对应内容**

```tsx
const [documentBlocksByFileId, setDocumentBlocksByFileId] = useState<Record<string, ContentBlock[]>>({});

const applyViewerState = useCallback((fileId: string | null) => {
  if (!fileId) {
    dispatch({ type: "SET_LANG_DATA", sections: [], contentBlocks: [] });
    dispatch({ type: "SELECT_SECTION", sectionId: null });
    return;
  }

  const file = files.find((item) => item.id === fileId);
  const blocks = documentBlocksByFileId[fileId] ?? [];
  dispatch({ type: "SET_LANG_DATA", sections: [], contentBlocks: blocks });

  if (file?.viewerStatus === "ready") {
    dispatch({ type: "SELECT_SECTION", sectionId: UPLOADED_CONTENT_SECTION_ID });
  } else {
    dispatch({ type: "SELECT_SECTION", sectionId: null });
  }
}, [documentBlocksByFileId, files]);

const handleFileSelect = useCallback((fileId: string, fileName: string) => {
  setSelectedFileId(fileId);
  setSelectedFileName(fileName);
  setLeftMode("sections");
  applyViewerState(fileId);
}, [applyViewerState]);
```

- [ ] **Step 5: 上传成功后回填 `documentId`，并把结果缓存到对应文件**

```tsx
const detail = await getDocumentDetail(uploadResult.id);
const blocks = unitsToContentBlocks(detail.units);

setDocumentBlocksByFileId((prev) => ({ ...prev, [fileId]: blocks }));
setFiles((prev) =>
  prev.map((f) =>
    f.id === fileId
      ? {
          ...f,
          status: "parsed",
          documentId: uploadResult.id,
          viewerStatus: blocks.length > 0 ? "ready" : "empty",
        }
      : f,
  ),
);
```

- [ ] **Step 6: 运行测试确认切换文件行为已通过**

Run: `rtk npm run test:frontend -- WorkspacePage.test.tsx`

Expected: PASS，新增用例可以在 A / B 两份文件之间来回切换且显示各自内容。

- [ ] **Step 7: 提交本任务**

```bash
git add src/features/workspace/type.ts src/features/workspace/pages/WorkspacePage.tsx src/features/workspace/pages/WorkspacePage.test.tsx
git commit -m "fix: map uploaded files to parsed content"
```

### Task 2: 清理旧查看器状态并显式渲染空结果/错误状态

**Files:**
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`
- Modify: `src/features/workspace/components/center/DocumentViewer.tsx`
- Test: `src/features/workspace/pages/WorkspacePage.test.tsx`

- [ ] **Step 1: 写失败测试，覆盖上传失败后旧内容不应残留、空 `units` 不应一直显示“解析中”**

```tsx
it("上传失败后清空中央区域旧内容并显示错误提示", async () => {
  render(<WorkspacePage initialFiles={sampleFiles} initialSections={sampleSections} initialContentBlocks={sampleContentBlocks} initialFootnotes={sampleFootnotes} />);

  fireEvent.click(screen.getByText("cours-analyse-s1.pdf"));
  fireEvent.click(screen.getByText((c) => c.includes("1.1 背景介绍")));
  expect(screen.getByText("近年来，人工智能技术取得了飞速发展。")).toBeDefined();

  (uploadDocument as Mock).mockRejectedValue(new Error("网络错误"));
  await uploadPdf("broken.pdf");

  expect(await screen.findByText(/上传失败：网络错误/)).toBeDefined();
  expect(screen.queryByText("近年来，人工智能技术取得了飞速发展。")).toBeNull();
});

it("解析成功但 units 为空时显示空结果提示", async () => {
  (uploadDocument as Mock).mockResolvedValue({ id: "doc-empty" });
  (getDocumentDetail as Mock).mockResolvedValue({
    document: { id: "doc-empty", title: "empty" },
    units: [],
  });

  render(<WorkspacePage />);
  await uploadPdf("empty.pdf");

  expect(await screen.findByText("《empty.pdf》解析完成，但暂时没有可展示文本")).toBeDefined();
});
```

- [ ] **Step 2: 运行单测确认当前实现失败**

Run: `rtk npm run test:frontend -- WorkspacePage.test.tsx`

Expected: FAIL，旧内容仍残留，或空结果时仍显示“解析中，请稍候…”。

- [ ] **Step 3: 在 `WorkspacePage` 中显式维护当前查看器状态**

```tsx
const [viewerStatus, setViewerStatus] = useState<ViewerStatus>("idle");

const resetViewer = useCallback((status: ViewerStatus) => {
  dispatch({ type: "SET_LANG_DATA", sections: [], contentBlocks: [] });
  dispatch({ type: "SELECT_SECTION", sectionId: null });
  setViewerStatus(status);
}, []);

setFiles((prev) => [
  { ...newFile, viewerStatus: "parsing" },
  ...prev,
]);
resetViewer("parsing");

// success
setViewerStatus(blocks.length > 0 ? "ready" : "empty");

// error
resetViewer("error");
```

- [ ] **Step 4: 让 `DocumentViewer` 基于 `viewerStatus` 渲染不同空态**

```tsx
type DocumentViewerProps = {
  viewerStatus: ViewerStatus;
  pendingFileName?: string;
  errorMessage?: string | null;
  // ...existing props
};

if (viewerStatus === "idle") {
  return <EmptyState title="从左侧上传一份文档开始" subtitle="支持 PDF、Word、PPT、图片、TXT 和 Markdown" />;
}

if (viewerStatus === "parsing") {
  return <EmptyState title={`《${pendingFileName}》已上传，等待解析`} subtitle="解析中，请稍候…" />;
}

if (viewerStatus === "empty") {
  return <EmptyState title={`《${pendingFileName}》解析完成，但暂时没有可展示文本`} subtitle="可以稍后补充 OCR / 版面解析能力" />;
}

if (viewerStatus === "error") {
  return <EmptyState title="文档上传失败" subtitle={errorMessage ?? "请稍后重试"} />;
}
```

- [ ] **Step 5: 运行测试确认旧内容不会残留，空结果也能正确提示**

Run: `rtk npm run test:frontend -- WorkspacePage.test.tsx`

Expected: PASS，失败上传后中央区域不再显示旧文档内容，空 `units` 时展示“解析完成但暂无内容”。

- [ ] **Step 6: 提交本任务**

```bash
git add src/features/workspace/pages/WorkspacePage.tsx src/features/workspace/components/center/DocumentViewer.tsx src/features/workspace/pages/WorkspacePage.test.tsx
git commit -m "fix: render viewer states explicitly"
```

### Task 3: 收紧 API 契约与错误处理

**Files:**
- Modify: `src/types/document.ts`
- Modify: `src/features/document/api/documentApi.ts`
- Modify: `src/lib/apiClient.ts`
- Test: `src/features/document/api/documentApi.test.ts`
- Test: `src/lib/apiClient.test.ts`

- [ ] **Step 1: 写失败测试，覆盖 422 数组错误和 `workspace_id` 编码**

```ts
it("HTTP 422 detail 为数组时拼出可读错误", async () => {
  globalThis.fetch = vi.fn().mockResolvedValue(
    new Response(
      JSON.stringify({ detail: [{ loc: ["body", "workspace_id"], msg: "Field required" }] }),
      { status: 422, statusText: "Unprocessable Entity" },
    ),
  ) as unknown as typeof fetch;

  await expect(request("/documents/upload")).rejects.toThrow(/workspace_id/);
  await expect(request("/documents/upload")).rejects.toThrow(/Field required/);
});

it("listDocuments 对 workspace_id 做 URL 编码", async () => {
  (request as ReturnType<typeof vi.fn>).mockResolvedValue([]);
  await listDocuments("cours & notes");
  expect(request).toHaveBeenCalledWith("/documents?workspace_id=cours%20%26%20notes");
});
```

- [ ] **Step 2: 运行单测确认当前实现失败**

Run: `rtk npm run test:frontend -- apiClient.test.ts documentApi.test.ts`

Expected: FAIL，`request` 无法解包数组 `detail`，`listDocuments` 直接拼原始字符串。

- [ ] **Step 3: 对齐前端类型与后端 schema**

```ts
export interface DocumentSummary {
  id: string;
  workspace_id: string;
  title: string;
  original_filename: string;
  file_type: string;
  status: string;
  page_count: number | null;
  created_at: string;
}

export interface DocumentUploadResponse {
  id: string;
  title: string;
  original_filename: string;
  file_type: string;
  status: string;
  page_count: number | null;
  created_at: string;
}
```

- [ ] **Step 4: 修正 `documentApi` 的列表函数**

```ts
export async function listDocuments(workspaceId: string): Promise<DocumentSummary[]> {
  const encodedWorkspaceId = encodeURIComponent(workspaceId);
  return request(`/documents?workspace_id=${encodedWorkspaceId}`);
}
```

- [ ] **Step 5: 让 `apiClient` 兼容字符串、数组、对象三种 `detail` 结构**

```ts
function normalizeErrorDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const loc = Array.isArray((item as { loc?: unknown }).loc)
            ? (item as { loc: unknown[] }).loc.join(".")
            : "unknown";
          const msg = typeof (item as { msg?: unknown }).msg === "string"
            ? (item as { msg: string }).msg
            : JSON.stringify(item);
          return `${loc}: ${msg}`;
        }
        return String(item);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return fallback;
}
```

- [ ] **Step 6: 运行相关测试确认契约已收紧**

Run: `rtk npm run test:frontend -- apiClient.test.ts documentApi.test.ts`

Expected: PASS，422 错误信息包含字段路径和消息，列表接口对特殊字符编码。

- [ ] **Step 7: 提交本任务**

```bash
git add src/types/document.ts src/features/document/api/documentApi.ts src/lib/apiClient.ts src/features/document/api/documentApi.test.ts src/lib/apiClient.test.ts
git commit -m "fix: align document api contracts"
```

### Task 4: 全量验证

**Files:**
- Modify: none
- Test: `src/features/workspace/pages/WorkspacePage.test.tsx`
- Test: `src/features/document/api/documentApi.test.ts`
- Test: `src/lib/apiClient.test.ts`

- [ ] **Step 1: 运行前端测试**

Run: `rtk npm run test:frontend`

Expected: PASS，所有 Vitest 用例通过。

- [ ] **Step 2: 运行类型检查**

Run: `npx tsc --noEmit`

Expected: PASS，无 TypeScript 错误输出。

- [ ] **Step 3: 手工联调验证开发态上传**

Run: `Test-Path -LiteralPath "backend-python"; if ($?) { python -m uvicorn app.main:app --port 8000 }`
Workdir: `D:\开发work\greenbean-study-assistant\backend-python`

Run: `npm run dev`
Workdir: `D:\开发work\greenbean-study-assistant`

Expected:
- 上传 `a.pdf` 后显示 A 的分页文本
- 再上传 `b.pdf` 后显示 B 的分页文本
- 点回 `a.pdf` 时恢复 A 的内容
- 触发失败上传时中央区域不残留旧内容

- [ ] **Step 4: 提交验证结论**

```bash
git status --short
git diff --stat
```

Expected: 仅包含本计划涉及的前端文件改动，无额外意外变更。

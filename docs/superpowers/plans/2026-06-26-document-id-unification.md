# Document ID Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every persisted document in the workspace use the backend `documentId` as its single frontend identity so delete, restore, selection, and caches stay consistent.

**Architecture:** Keep temporary IDs only during the upload-in-progress phase. As soon as upload succeeds, replace the temporary file item ID with the backend document ID, migrate any cached state to that real ID, and make restore/delete logic merge and remove items by persisted document ID.

**Tech Stack:** React 19, TypeScript, Vitest, Testing Library, existing workspace state in `WorkspacePage`, existing document API mocks.

---

## File Map

- Modify: `src/features/workspace/pages/WorkspacePage.tsx`
  - Add small helper functions for persisted document identity, restored-file dedupe, cache migration, and document-state cleanup.
  - Converge uploaded file items from temporary IDs to backend `documentId`.
  - Make restored documents merge idempotently by persisted document ID.
  - Make delete remove all local records and caches for the same persisted document.
- Modify: `src/features/workspace/pages/WorkspacePage.test.tsx`
  - Import and mock `listDocuments` and `deleteDocument` explicitly.
  - Add regression coverage for restored-list dedupe and immediate removal after delete.

## Task 1: Lock the Regression with WorkspacePage Tests

**Files:**
- Modify: `src/features/workspace/pages/WorkspacePage.test.tsx`

- [ ] **Step 1: Expand document API imports for the new tests**

Update the import at the top of `src/features/workspace/pages/WorkspacePage.test.tsx`:

```ts
import {
  uploadDocument,
  getDocumentDetail,
  listDocuments,
  deleteDocument,
} from "../../document/api/documentApi";
```

- [ ] **Step 2: Add a failing regression test for persisted-document dedupe after restore**

Add this test near the existing upload/reselect tests in `src/features/workspace/pages/WorkspacePage.test.tsx`:

```tsx
  it("上传成功后使用真实 documentId，恢复列表时不会重复显示同一文档", async () => {
    (uploadDocument as Mock).mockResolvedValueOnce({ id: "doc-1" });
    (getDocumentDetail as Mock).mockResolvedValueOnce({
      document: { id: "doc-1", title: "doc-1" },
      units: [{ id: "u1", sequence_index: 0, page_number: 1, text_content: "第一页内容" }],
    });
    (listDocuments as Mock).mockResolvedValue([
      {
        id: "doc-1",
        workspace_id: "workspace_1",
        title: "lecture",
        original_filename: "lecture.pdf",
        file_type: "pdf",
        status: "parsed",
        page_count: 1,
        created_at: "2026-06-26T12:00:00Z",
      },
    ]);

    render(<WorkspacePage />);
    await uploadPdf("lecture.pdf");

    await waitFor(() => {
      expect(screen.getAllByText("lecture.pdf")).toHaveLength(1);
    });
  });
```

- [ ] **Step 3: Add a failing regression test for immediate removal after delete**

Add this test after the dedupe test in `src/features/workspace/pages/WorkspacePage.test.tsx`:

```tsx
  it("删除已持久化文档后立即移除该 documentId 的所有本地记录", async () => {
    (uploadDocument as Mock).mockResolvedValueOnce({ id: "doc-1" });
    (getDocumentDetail as Mock).mockResolvedValueOnce({
      document: { id: "doc-1", title: "doc-1" },
      units: [{ id: "u1", sequence_index: 0, page_number: 1, text_content: "第一页内容" }],
    });
    (listDocuments as Mock).mockResolvedValue([
      {
        id: "doc-1",
        workspace_id: "workspace_1",
        title: "lecture",
        original_filename: "lecture.pdf",
        file_type: "pdf",
        status: "parsed",
        page_count: 1,
        created_at: "2026-06-26T12:00:00Z",
      },
    ]);
    (deleteDocument as Mock).mockResolvedValue(undefined);

    render(<WorkspacePage />);
    await uploadPdf("lecture.pdf");

    const fileButton = await screen.findByText("lecture.pdf");
    fireEvent.contextMenu(fileButton.closest("button") as HTMLElement);
    fireEvent.click(screen.getByText("删除"));

    await waitFor(() => {
      expect(screen.queryByText("lecture.pdf")).toBeNull();
    });
    expect(deleteDocument).toHaveBeenCalledWith("doc-1");
  });
```

- [ ] **Step 4: Run the workspace page tests and verify Red**

Run: `rtk npm test -- src/features/workspace/pages/WorkspacePage.test.tsx --runInBand`

Expected: FAIL because the current implementation can keep both the temporary file ID entry and the restored `doc.id` entry, and delete only filters one `fileId`.

## Task 2: Converge Persisted Documents to the Backend ID

**Files:**
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`

- [ ] **Step 1: Add focused helpers for persisted identity and cache cleanup**

Add these helpers near the top of `src/features/workspace/pages/WorkspacePage.tsx`, after the imports and before `workspaceReducer`:

```ts
function getPersistedDocumentId(file: Pick<FileItem, "id" | "documentId">): string | null {
  return file.documentId ?? (file.id.startsWith("f_") ? null : file.id);
}

function mergeRestoredFiles(currentFiles: FileItem[], restoredFiles: FileItem[]): FileItem[] {
  const next = [...currentFiles];

  for (const restoredFile of restoredFiles) {
    const restoredDocumentId = getPersistedDocumentId(restoredFile);
    const existingIndex = next.findIndex((file) => getPersistedDocumentId(file) === restoredDocumentId);

    if (existingIndex >= 0) {
      next[existingIndex] = {
        ...next[existingIndex],
        ...restoredFile,
        id: restoredFile.id,
        documentId: restoredFile.documentId,
      };
      continue;
    }

    next.push(restoredFile);
  }

  return next;
}

function removeFileStateByKey<T>(state: Record<string, T>, fileKey: string): Record<string, T> {
  const next = { ...state };
  delete next[fileKey];
  return next;
}
```

- [ ] **Step 2: Make restored documents merge idempotently by real document ID**

Replace the restore branch in `src/features/workspace/pages/WorkspacePage.tsx:184` from:

```ts
        setFiles((prev) => [...restoredFiles, ...prev]);
```

to:

```ts
        setFiles((prev) => mergeRestoredFiles(prev, restoredFiles));
```

Keep the restored item mapping aligned to the real backend ID:

```ts
        const restoredFiles: FileItem[] = docs.map((doc) => ({
          id: doc.id,
          name: doc.original_filename,
          type: getFileType(doc.original_filename),
          category: "",
          size: "",
          date: doc.created_at.split("T")[0],
          status: "parsed",
          documentId: doc.id,
          viewerStatus: "ready",
        }));
```

- [ ] **Step 3: Converge upload success from temporary ID to real document ID**

Inside the upload success branch in `src/features/workspace/pages/WorkspacePage.tsx`, replace the file update block with this minimal convergence logic:

```ts
      const persistedFileId = uploadResult.id;

      setDocumentBlocksByFileId((prev) => ({
        ...removeFileStateByKey(prev, fileId),
        [persistedFileId]: blocks,
      }));
      setDocumentSectionsByFileId((prev) => ({
        ...removeFileStateByKey(prev, fileId),
        [persistedFileId]: sections,
      }));
      setDocumentUnitsByFileId((prev) => ({
        ...removeFileStateByKey(prev, fileId),
        [persistedFileId]: detail.units,
      }));
      setVisibleUnitsByFileId((prev) => ({
        ...removeFileStateByKey(prev, fileId),
        [persistedFileId]: visibleUnits,
      }));

      setSelectedFileId(persistedFileId);
      setFiles((prev) =>
        prev.map((f) => (f.id === fileId ? {
          ...f,
          id: persistedFileId,
          status: "parsed",
          documentId: persistedFileId,
          viewerStatus: detail.units.length > 0 || sections.length > 0 ? "ready" : "empty",
        } : f)),
      );
```

- [ ] **Step 4: Make delete remove all local records for the same persisted document**

Replace the delete branch in `src/features/workspace/pages/WorkspacePage.tsx:399` with this logic:

```ts
  const handleDeleteFile = useCallback(async (fileId: string) => {
    const file = files.find((f) => f.id === fileId);
    const persistedDocumentId = file ? getPersistedDocumentId(file) : null;

    if (persistedDocumentId) {
      try {
        await deleteDocument(persistedDocumentId);
      } catch (err) {
        setUploadError(err instanceof Error ? err.message : "文档删除失败");
        return;
      }
    }

    setFiles((prev) => prev.filter((f) => {
      const candidateDocumentId = getPersistedDocumentId(f);
      if (persistedDocumentId) {
        return candidateDocumentId !== persistedDocumentId;
      }
      return f.id !== fileId;
    }));

    const stateKey = persistedDocumentId ?? fileId;
    setDocumentBlocksByFileId((prev) => removeFileStateByKey(prev, stateKey));
    setDocumentSectionsByFileId((prev) => removeFileStateByKey(prev, stateKey));
    setDocumentUnitsByFileId((prev) => removeFileStateByKey(prev, stateKey));
    setVisibleUnitsByFileId((prev) => removeFileStateByKey(prev, stateKey));

    if (selectedFileId === fileId || selectedFileId === persistedDocumentId) {
      setSelectedFileId(null);
      setSelectedFileName("");
      setLeftMode("files");
      applyFileContent(null);
    }
  }, [applyFileContent, files, selectedFileId]);
```

- [ ] **Step 5: Run the workspace page tests and verify Green**

Run: `rtk npm test -- src/features/workspace/pages/WorkspacePage.test.tsx --runInBand`

Expected: PASS, including the two new regressions for dedupe and immediate delete refresh.

## Task 3: Run Focused Verification

**Files:**
- No code changes

- [ ] **Step 1: Run the workspace page suite again as the final focused check**

Run: `rtk npm test -- src/features/workspace/pages/WorkspacePage.test.tsx --runInBand`

Expected: PASS.

- [ ] **Step 2: Run the workspace-related component tests to catch collateral regressions**

Run: `rtk npm test -- src/features/workspace/components/left/FileManager.test.tsx src/features/workspace/components/center/DocumentViewer.test.tsx --runInBand`

Expected: PASS.

- [ ] **Step 3: Inspect the changed files before handoff**

Run: `git diff -- src/features/workspace/pages/WorkspacePage.tsx src/features/workspace/pages/WorkspacePage.test.tsx docs/superpowers/plans/2026-06-26-document-id-unification.md`

Expected: Diff shows only the planned ID-unification fix, regression tests, and this plan file.

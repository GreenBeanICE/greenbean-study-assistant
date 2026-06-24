# Empty Workspace Upload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove production demo workspace data and make single-file upload create a selected pending document shown in the document viewer.

**Architecture:** `WorkspacePage` becomes the owner of runtime files and upload state. `FileManager` renders only props-provided files and reports upload/file actions upward. `DocumentViewer` gets a `pendingFileName` prop for the waiting-for-parser state.

**Tech Stack:** React 19, TypeScript, Vitest, Testing Library, Vite.

---

## Scope

Included:
- Clear production demo files, sections, content blocks, footnotes, and default document title.
- Keep sample data only inside tests.
- Add controlled upload flow from `FileManager` to `WorkspacePage`.
- Add `DocumentViewer` empty state and pending parse state.
- Update affected frontend tests.

Excluded:
- Do not modify `src/features/workspace/components/right/ChatPanel.tsx` or `ChatPanel.test.tsx` in this task.
- Do not connect Python ingest, database persistence, RAG, or Tauri commands.
- Do not add multiple-file upload.

## File Structure

- Modify `src/features/workspace/type.ts`: add shared file/folder types, upload callbacks, initial test-data props, and `pendingFileName`.
- Modify `src/features/workspace/components/left/FileManager.tsx`: remove production demo files and make file mutations callback-driven.
- Modify `src/features/workspace/components/center/DocumentViewer.tsx`: add initial empty and pending parse states.
- Modify `src/features/workspace/pages/WorkspacePage.tsx`: own `files`, upload handling, and empty initial reducer state.
- Modify `src/features/workspace/components/left/FileManager.test.tsx`: use local test fixtures instead of production defaults.
- Modify `src/features/workspace/components/center/DocumentViewer.test.tsx`: assert empty and pending states.
- Modify `src/features/workspace/pages/WorkspacePage.test.tsx`: use explicit fixtures for legacy interaction tests and add empty/upload coverage.

---

### Task 1: Shared Types And Test Expectations

**Files:**
- Modify: `src/features/workspace/type.ts`
- Test: `src/features/workspace/components/center/DocumentViewer.test.tsx`

- [ ] **Step 1: Write failing DocumentViewer pending-state tests**

Update `src/features/workspace/components/center/DocumentViewer.test.tsx` so these tests are present and expect the target behavior:

```tsx
it("未选择章节且无 pendingFileName 时显示初始空状态文案", () => {
  render(<DocumentViewer {...defaultProps} />);
  expect(screen.getByText("从左侧上传一份文档开始")).toBeDefined();
});

it("pendingFileName 有值时显示等待解析状态", () => {
  render(<DocumentViewer {...defaultProps} pendingFileName="lecture.pdf" />);
  expect(screen.getByText("《lecture.pdf》已上传，等待解析")).toBeDefined();
});

it("pendingFileName 有值时显示解析未接入提示", () => {
  render(<DocumentViewer {...defaultProps} pendingFileName="lecture.pdf" />);
  expect(screen.getByText("解析能力尚未接入，刷新后需要重新上传")).toBeDefined();
});
```

- [ ] **Step 2: Run focused test to verify failure**

Run:

```powershell
rtk npm test -- src/features/workspace/components/center/DocumentViewer.test.tsx
```

Expected: FAIL because `DocumentViewerProps` has no `pendingFileName` and the component still renders `选择章节查看内容`.

- [ ] **Step 3: Add shared types**

Update `src/features/workspace/type.ts` with file/folder types and prop extensions:

```ts
export type FileType = "PDF" | "DOC" | "PPT" | "IMG" | "TXT" | "MD";
export type FileStatus = "parsed" | "parsing" | "pending";

export interface FileItem {
  id: string;
  name: string;
  type: FileType;
  category: string;
  size: string;
  date: string;
  status: FileStatus;
}

export interface Folder {
  key: string;
  label: string;
}
```

Extend `DocumentViewerProps`:

```ts
export interface DocumentViewerProps {
  contentBlocks: ContentBlock[];
  selectedSectionId: string | null;
  pendingFileName?: string;
  footnotes: FootnoteReference[];
  expandedFootnoteId: string | null;
  currentSelection: TextSelection | null;
  showSelectionMenu: boolean;
  selectionMenuPos: { x: number; y: number } | null;
  onToggleHighlight: (blockId: string, lineId: string) => void;
  onUpdateLineText: (blockId: string, lineId: string, text: string) => void;
  onFormatLine: (blockId: string, lineId: string, format: TextFormatAction) => void;
  onToggleFootnote: (footnoteId: string) => void;
  onSelectText: (selection: TextSelection | null) => void;
  onShowSelectionMenu: (show: boolean, pos?: { x: number; y: number }) => void;
  onQuoteSelection: () => void;
}
```

Extend `WorkspacePageProps`:

```ts
export interface WorkspacePageProps {
  workspaceId?: string;
  initialFiles?: FileItem[];
  initialFolders?: Folder[];
  initialSections?: SectionNode[];
  initialContentBlocks?: ContentBlock[];
  initialFootnotes?: FootnoteReference[];
}
```

- [ ] **Step 4: Run focused type/test check**

Run:

```powershell
rtk npm test -- src/features/workspace/components/center/DocumentViewer.test.tsx
```

Expected: still FAIL until `DocumentViewer` renders the new states.

---

### Task 2: DocumentViewer Empty And Pending States

**Files:**
- Modify: `src/features/workspace/components/center/DocumentViewer.tsx`
- Test: `src/features/workspace/components/center/DocumentViewer.test.tsx`

- [ ] **Step 1: Implement pending-state rendering**

Update the component signature in `DocumentViewer.tsx`:

```tsx
function DocumentViewer({
  contentBlocks, selectedSectionId, pendingFileName, footnotes, expandedFootnoteId,
  currentSelection, showSelectionMenu, selectionMenuPos,
  onToggleHighlight, onUpdateLineText, onFormatLine, onToggleFootnote,
  onSelectText, onShowSelectionMenu, onQuoteSelection,
}: DocumentViewerProps) {
```

Replace the empty-state text block with this conditional content:

```tsx
{showEmptyState ? (
  <div className="inline-block pt-16 pl-6">
    <div className="w-16 h-16 rounded-2xl bg-black/5 flex items-center justify-center mb-4">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" className="text-neutral-400">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    </div>
    <p className="text-sm text-neutral-500 font-medium">
      {pendingFileName ? `《${pendingFileName}》已上传，等待解析` : "从左侧上传一份文档开始"}
    </p>
    <p className="text-xs text-neutral-400 mt-1">
      {pendingFileName ? "解析能力尚未接入，刷新后需要重新上传" : "支持 PDF、Word、PPT、图片、TXT 和 Markdown"}
    </p>
  </div>
) : (
```

- [ ] **Step 2: Run focused DocumentViewer tests**

Run:

```powershell
rtk npm test -- src/features/workspace/components/center/DocumentViewer.test.tsx
```

Expected: PASS for `DocumentViewer.test.tsx`.

---

### Task 3: Controlled FileManager

**Files:**
- Modify: `src/features/workspace/components/left/FileManager.tsx`
- Test: `src/features/workspace/components/left/FileManager.test.tsx`

- [ ] **Step 1: Convert tests to explicit fixtures**

At the top of `FileManager.test.tsx`, define local fixtures:

```tsx
const sampleFolders: Folder[] = [
  { key: "course", label: "课程资料" },
  { key: "exam", label: "考试复习" },
  { key: "thesis", label: "论文参考" },
];

const sampleFiles: FileItem[] = [
  { id: "f1", name: "cours-analyse-s1.pdf", type: "PDF", category: "course", size: "12.4 MB", date: "2025-09-15", status: "parsed" },
  { id: "f2", name: "TD-economie-chap2.docx", type: "DOC", category: "course", size: "3.2 MB", date: "2025-10-02", status: "parsed" },
  { id: "f3", name: "cours-droit-commercial.pptx", type: "PPT", category: "course", size: "45.8 MB", date: "2025-10-10", status: "parsing" },
  { id: "f4", name: "cours-maths-tableau.webp", type: "IMG", category: "", size: "2.1 MB", date: "2025-10-15", status: "pending" },
  { id: "f5", name: "复习笔记-期中exam.pdf", type: "PDF", category: "exam", size: "8.5 MB", date: "2025-11-01", status: "parsed" },
  { id: "f6", name: "论文-引言部分.docx", type: "DOC", category: "thesis", size: "1.8 MB", date: "2025-11-10", status: "parsed" },
];

function renderFileManager(props: Partial<React.ComponentProps<typeof FileManager>> = {}) {
  return render(
    <FileManager
      files={sampleFiles}
      folders={sampleFolders}
      onUpload={vi.fn()}
      {...props}
    />,
  );
}
```

Change legacy `render(<FileManager />)` tests that depend on sample files to `renderFileManager()`.

Add a default-empty test:

```tsx
it("默认不渲染任何生产演示文件", () => {
  render(<FileManager files={[]} folders={sampleFolders} onUpload={vi.fn()} />);
  expect(screen.queryByText("cours-analyse-s1.pdf")).toBeNull();
});
```

Add upload callback test:

```tsx
it("上传新文件调用 onUpload", () => {
  const onUpload = vi.fn();
  render(<FileManager files={[]} folders={sampleFolders} onUpload={onUpload} />);
  const uploadLabel = screen.getByTitle("上传新文件");
  const fileInput = uploadLabel.querySelector('input[type="file"]') as HTMLInputElement;
  const file = new File(["dummy content"], "nouveau-cours.pdf", { type: "application/pdf" });
  Object.defineProperty(fileInput, "files", { value: [file] });
  fireEvent.change(fileInput);
  expect(onUpload).toHaveBeenCalledWith(file);
});
```

- [ ] **Step 2: Run FileManager tests to verify failure**

Run:

```powershell
rtk npm test -- src/features/workspace/components/left/FileManager.test.tsx
```

Expected: FAIL because `FileManager` still owns default internal files and has no required `onUpload` callback.

- [ ] **Step 3: Implement controlled FileManager props**

In `FileManager.tsx`, remove local `FileType`, `FileStatus`, `FileItem`, and `Folder` declarations and import them:

```tsx
import type { FileItem, FileManagerProps, FileType, Folder } from "../../type";
```

Add `FileManagerProps` to `type.ts`:

```ts
export interface FileManagerProps {
  files: FileItem[];
  folders?: Folder[];
  selectedFileId?: string | null;
  onUpload: (file: File) => void;
  onFileSelect?: (fileId: string) => void;
  onFileSelectWithName?: (fileId: string, fileName: string) => void;
  onDeleteFile?: (fileId: string) => void;
  onRenameFile?: (fileId: string, newName: string) => void;
  onMoveFile?: (fileId: string, toCategory: string) => void;
}
```

Change the component setup:

```tsx
export default function FileManager({
  files,
  folders = [],
  selectedFileId,
  onUpload,
  onFileSelect,
  onFileSelectWithName,
  onDeleteFile,
  onRenameFile,
  onMoveFile,
}: FileManagerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(["course"]));
```

Use `files` everywhere instead of `allFiles` and remove `internalFiles`, `DEFAULT_FOLDERS`, `getDefaultFiles`, and `uid`.

Change callbacks:

```tsx
const handleUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (file) {
    onUpload(file);
  }
  e.target.value = "";
}, [onUpload]);

const handleDelete = useCallback((fileId: string) => {
  onDeleteFile?.(fileId);
  closeContextMenu();
}, [closeContextMenu, onDeleteFile]);

const handleRenameSubmit = useCallback(() => {
  if (renaming && renaming.name.trim()) {
    onRenameFile?.(renaming.fileId, renaming.name.trim());
  }
  setRenaming(null);
}, [onRenameFile, renaming]);

const handleMove = useCallback((fileId: string, toCategory: string) => {
  onMoveFile?.(fileId, toCategory);
  closeContextMenu();
}, [closeContextMenu, onMoveFile]);
```

- [ ] **Step 4: Run FileManager tests**

Run:

```powershell
rtk npm test -- src/features/workspace/components/left/FileManager.test.tsx
```

Expected: PASS after test expectations are updated to controlled behavior.

---

### Task 4: WorkspacePage Owns Empty Files And Upload Flow

**Files:**
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`
- Test: `src/features/workspace/pages/WorkspacePage.test.tsx`

- [ ] **Step 1: Add WorkspacePage tests for empty production state**

Add or update tests in `WorkspacePage.test.tsx`:

```tsx
it("默认进入空工作区时不显示演示文件", () => {
  render(<WorkspacePage />);
  expect(screen.queryByText("cours-analyse-s1.pdf")).toBeNull();
  expect(screen.getByText("从左侧上传一份文档开始")).toBeDefined();
});

it("上传文档后进入等待解析态", () => {
  render(<WorkspacePage />);
  const uploadLabel = screen.getByTitle("上传新文件");
  const fileInput = uploadLabel.querySelector('input[type="file"]') as HTMLInputElement;
  const file = new File(["lecture"], "lecture.pdf", { type: "application/pdf" });
  Object.defineProperty(fileInput, "files", { value: [file] });
  fireEvent.change(fileInput);
  expect(screen.getByText("暂无章节数据")).toBeDefined();
  expect(screen.getByText("《lecture.pdf》已上传，等待解析")).toBeDefined();
});
```

For legacy tests that need demo data, define local fixtures in the test file and render with:

```tsx
render(
  <WorkspacePage
    initialFiles={sampleFiles}
    initialFolders={sampleFolders}
    initialSections={sampleSections}
    initialContentBlocks={sampleContentBlocks}
    initialFootnotes={sampleFootnotes}
  />,
);
```

- [ ] **Step 2: Run WorkspacePage tests to verify failure**

Run:

```powershell
rtk npm test -- src/features/workspace/pages/WorkspacePage.test.tsx
```

Expected: FAIL because `WorkspacePage` still initializes demo data and `FileManager` props have not been wired.

- [ ] **Step 3: Implement empty WorkspacePage state and upload owner**

In `WorkspacePage.tsx`, remove `getLocalizedSections`, `getLocalizedContent`, and `initialFootnotes` from production code.

Add helpers near the component:

```tsx
const DEFAULT_FOLDERS: Folder[] = [
  { key: "course", label: "课程资料" },
  { key: "exam", label: "考试复习" },
  { key: "thesis", label: "论文参考" },
];

function createFileId(): string {
  const array = new Uint32Array(1);
  crypto.getRandomValues(array);
  return `f_${array[0].toString(36).slice(0, 7)}`;
}

function getFileType(fileName: string): FileType {
  const ext = fileName.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "PDF";
  if (ext === "doc" || ext === "docx") return "DOC";
  if (ext === "ppt" || ext === "pptx") return "PPT";
  if (["png", "jpg", "jpeg", "webp"].includes(ext ?? "")) return "IMG";
  if (ext === "md") return "MD";
  return "TXT";
}

function formatFileSize(bytes: number): string {
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
```

Change the component signature and state:

```tsx
function WorkspacePage({ initialFiles = [], initialFolders = DEFAULT_FOLDERS, initialSections = [], initialContentBlocks = [], initialFootnotes = [] }: WorkspacePageProps) {
  const [files, setFiles] = useState<FileItem[]>(initialFiles);
```

Initialize reducer with empty/default props:

```tsx
const [state, dispatch] = useReducer(workspaceReducer, {
  sections: initialSections,
  selectedSectionId: null,
  contentBlocks: initialContentBlocks,
  chatMessages: [],
  chatInput: "",
  loading: false,
  footnotes: initialFootnotes,
  expandedFootnoteId: null,
  currentSelection: null,
  showSelectionMenu: false,
  selectionMenuPos: null,
  quotedText: null,
  tokenUsage: 0,
  leftCollapsed: false,
  rightCollapsed: false,
  leftPanelWidth: 256,
  rightPanelWidth: 302,
  documentTitle: "",
});
```

Add upload and file action handlers:

```tsx
const handleUpload = useCallback((file: File) => {
  const newFile: FileItem = {
    id: createFileId(),
    name: file.name,
    type: getFileType(file.name),
    category: "",
    size: formatFileSize(file.size),
    date: new Date().toISOString().split("T")[0],
    status: "pending",
  };
  setFiles((prev) => [newFile, ...prev]);
  setSelectedFileId(newFile.id);
  setSelectedFileName(newFile.name);
  setLeftMode("sections");
}, []);

const handleDeleteFile = useCallback((fileId: string) => {
  setFiles((prev) => prev.filter((file) => file.id !== fileId));
  if (selectedFileId === fileId) {
    setSelectedFileId(null);
    setSelectedFileName("");
    setLeftMode("files");
  }
}, [selectedFileId]);

const handleRenameFile = useCallback((fileId: string, newName: string) => {
  setFiles((prev) => prev.map((file) => file.id === fileId ? { ...file, name: newName } : file));
  if (selectedFileId === fileId) {
    setSelectedFileName(newName);
  }
}, [selectedFileId]);

const handleMoveFile = useCallback((fileId: string, toCategory: string) => {
  setFiles((prev) => prev.map((file) => file.id === fileId ? { ...file, category: toCategory } : file));
}, []);
```

Wire `FileManager`:

```tsx
<FileManager
  files={files}
  folders={initialFolders}
  selectedFileId={selectedFileId}
  onUpload={handleUpload}
  onFileSelectWithName={handleFileSelect}
  onDeleteFile={handleDeleteFile}
  onRenameFile={handleRenameFile}
  onMoveFile={handleMoveFile}
/>
```

Wire `DocumentViewer`:

```tsx
<DocumentViewer
  contentBlocks={state.contentBlocks}
  selectedSectionId={state.selectedSectionId}
  pendingFileName={selectedFileId && state.sections.length === 0 ? selectedFileName : undefined}
  footnotes={state.footnotes}
  expandedFootnoteId={state.expandedFootnoteId}
  currentSelection={state.currentSelection}
  showSelectionMenu={state.showSelectionMenu}
  selectionMenuPos={state.selectionMenuPos}
  onToggleHighlight={th}
  onUpdateLineText={ut}
  onFormatLine={fmt}
  onToggleFootnote={tf}
  onSelectText={sel}
  onShowSelectionMenu={sm}
  onQuoteSelection={qs}
/>
```

- [ ] **Step 4: Run WorkspacePage tests**

Run:

```powershell
rtk npm test -- src/features/workspace/pages/WorkspacePage.test.tsx
```

Expected: PASS after legacy tests receive fixtures and empty/upload tests match production behavior.

---

### Task 5: Regression Verification

**Files:**
- No code changes expected.

- [ ] **Step 1: Run focused workspace suite**

Run:

```powershell
rtk npm test -- src/features/workspace
```

Expected: PASS for workspace tests, except no assertions should require the old `ChatPanel` welcome copy change.

- [ ] **Step 2: Run frontend tests**

Run:

```powershell
rtk npm run test:frontend
```

Expected: PASS.

- [ ] **Step 3: Run build if tests pass**

Run:

```powershell
rtk npm run build
```

Expected: PASS with TypeScript/Vite build success.

---

## Self-Review

- Spec coverage: The plan covers empty production state, controlled single upload, pending parse state, local test fixtures, and excludes backend/RAG/Tauri work.
- User scope override: The plan intentionally excludes `ChatPanel` even though the older spec mentions it.
- Placeholder scan: No `TBD`/`TODO` implementation placeholders remain.
- Type consistency: `FileItem`, `Folder`, `FileType`, `FileManagerProps`, `WorkspacePageProps`, and `DocumentViewerProps` are defined before use.
- Verification: Uses `rtk` for test and build commands as requested.

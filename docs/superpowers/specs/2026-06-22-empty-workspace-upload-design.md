# 清空演示占位并提供文档上传入口

## 1. 背景与目标

当前 `workspace` 主交互壳已经具备左中右三栏骨架，但组件中深度嵌入了演示数据（假文件、假章节、假解析内容、模拟 AI 欢迎语），这些演示数据同时充当整个交互流程的脚手架。本次目标是：

- 清空所有演示占位，让用户进入一个真实空工作区；
- 提供左侧文件管理区的「上传文档」入口，上传文件后进入「等待解析」状态；
- 为后续接入 Python `ingest` API 保留清晰的接入点。

本任务只动前端运行时状态，刷新后丢失，不接后端、不写库、不接 RAG。

## 2. 范围

### 2.1 包含

- 清空 `WorkspacePage`、`FileManager` 中的演示数据（章节、内容块、脚注、文件、文件夹、文档标题、模拟聊天回复）；
- `FileManager` 受控化，文件列表与选中态提升到 `WorkspacePage`；
- 上传文件后自动选中并切换到章节树视图，中栏显示「等待解析」状态；
- 调整 `ChatPanel` 与 `DocumentViewer` 的空状态文案；
- 把现有演示数据抽取为测试夹具，复用现有交互测试。

### 2.2 排除（YAGNI）

- 不接 Python `ingest`、不写数据库、不接 RAG；
- 不加 `multiple` 批量上传（本次仅单文件）；
- 不提供「模拟解析」按钮——「等待解析」即终态，刷新丢失；
- 不删除右键菜单、重命名、移动、聊天发送等现有交互逻辑（保留以便后续接真实数据）；
- 不动 `SectionTree`、`ResizableHandle`、`DocumentToolbar` 组件本体；
- 不改 Tauri、后端、数据库。

## 3. 当前基线（演示数据位置）

| 文件 | 演示内容 | 位置 |
| --- | --- | --- |
| `WorkspacePage.tsx` | `getLocalizedSections()` 5 章假章节 | L12-31 |
| `WorkspacePage.tsx` | `getLocalizedContent()` 假内容块（AI 教育市场、对比表等） | L33-67 |
| `WorkspacePage.tsx` | `initialFootnotes` 假脚注 | L69-72 |
| `WorkspacePage.tsx` | 初始 `documentTitle: "cours-analyse-s1.pdf"` | L148 |
| `WorkspacePage.tsx` | `SEND_CHAT_MESSAGE` 模拟 AI 回复 | L113-117 |
| `FileManager.tsx` | `DEFAULT_FOLDERS`（课程资料/考试复习/论文参考） | L57-61 |
| `FileManager.tsx` | `getDefaultFiles()` 8 个假文件 | L63-75 |
| `FileManager.tsx` | 上传只更新内部 `internalFiles`，不通知父组件 | L148-163 |
| `DocumentViewer.tsx` | 空状态文案「选择章节查看内容」 | L321 |
| `ChatPanel.tsx` | 空状态欢迎语「有什么可以帮你？」 | L89 |

清空上述演示数据会让 `WorkspacePage.test.tsx`（60+ 用例）与 `FileManager.test.tsx`（30+ 用例）大量失败，本设计通过测试夹具方案（第 7 节）处理。

## 4. 架构决策

### 4.1 文件状态提升（受控化）

当前 `FileManager` 自持 `internalFiles`，`WorkspacePage` 不感知文件列表。为满足「上传后自动选中 + 切换章节树」，文件列表与选中态必须上提到 `WorkspacePage`。

采用受控方案：`FileManager` 改为纯 props 驱动，所有状态变更通过回调上抛，由 `WorkspacePage` 更新 `files`。这样：

- 单一数据源，与 `FileManager` 已有的 `externalFiles/externalFolders` 受控接口方向一致；
- 后续接入 Python `ingest` 时，只需把上传回调替换为 API 调用，组件结构不变（满足 AC6 接入点要求）。

### 4.2 中栏「等待解析」第三态

`DocumentViewer` 当前只有两种态：未选章节 / 已选章节内容。本次新增第三态：文件已选但未解析。通过新增 `pendingFileName?: string` prop 实现，渲染优先级：

1. `pendingFileName` 有值且 `selectedSectionId` 为空 → 显示「`《文件名》` 已上传，等待解析」；
2. 否则若 `selectedSectionId` 为空 → 显示初始空状态「从左侧上传一份文档开始」；
3. 否则显示章节内容。

### 4.3 测试夹具化

演示数据从生产组件抽离到测试夹具文件。`WorkspacePageProps` 增加可选初始数据 props，生产环境不传即空，测试传夹具即可复用现有交互用例。

## 5. 类型迁移

将 `FileItem`、`FileType`、`FileStatus`、`Folder` 从 `FileManager.tsx` 移到 `src/features/workspace/type.ts`。

理由：

- `WorkspacePage` 需要在 props 中持有 `files: FileItem[]`，避免页面层 props 类型反向依赖组件文件；
- 后续 `WorkspacePage` 的上传回调、右键回调签名都需要这些类型，统一在 `type.ts` 维护更清晰；
- 与同文件已有的 `WorkspaceState`、`WorkspacePageProps` 等类型集中。

## 6. 组件改动清单

### 6.1 `src/features/workspace/type.ts`

- 新增（迁入）：`FileType`、`FileStatus`、`FileItem`、`Folder`；
- 扩展 `WorkspacePageProps`：
  ```ts
  export interface WorkspacePageProps {
    workspaceId?: string;
    initialFiles?: FileItem[];
    initialSections?: SectionNode[];
    initialContentBlocks?: ContentBlock[];
    initialFootnotes?: FootnoteReference[];
  }
  ```
- 新增 `FileManagerProps` 接口（迁入并扩展）：
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
- 扩展 `DocumentViewerProps` 增加 `pendingFileName?: string`。

### 6.2 `src/features/workspace/pages/WorkspacePage.tsx`

- 删除 `getLocalizedSections`、`getLocalizedContent`、`initialFootnotes`、默认 `documentTitle`；
- 初始 reducer state：`sections: []`、`contentBlocks: []`、`footnotes: []`、`documentTitle: ""`；
- 新增 `files` state（初始 `props.initialFiles ?? []`）；
- 新增 `handleUpload(file: File)`：
  - 生成 `FileItem`（id、name、type、size、date、`status: "pending"`、`category: ""`）；
  - `setFiles([newFile, ...prev])`；
  - `setSelectedFileId(newFile.id)`、`setSelectedFileName(newFile.name)`、`setLeftMode("sections")`；
  - **接入点**：此处即后续替换为 Python `ingest` API 调用的位置；
- 新增 `handleDeleteFile / handleRenameFile / handleMoveFile`，操作 `files` state；
- 传 props 给 `FileManager`：`files`、`folders`（保留三个默认文件夹 `课程资料/考试复习/论文参考` 作为**空分类容器**，不内置任何文件）、`selectedFileId`、`onUpload`、`onFileSelectWithName`、`onDeleteFile`、`onRenameFile`、`onMoveFile`；
- 传 props 给 `DocumentViewer`：`pendingFileName={selectedFileId && state.sections.length === 0 ? selectedFileName : undefined}`；
- `SEND_CHAT_MESSAGE` reducer 分支本次**不动**（其中的模拟回复字符串仅在用户主动发消息时产生，不属于初始演示数据，保留作为后续接 AI 的占位）。

### 6.3 `src/features/workspace/components/left/FileManager.tsx`

- 删除 `DEFAULT_FOLDERS`、`getDefaultFiles`、`internalFiles` state、`uid`；
- 类型 import 改为从 `../../type` 引入；
- `files`、`folders` 改为必填 props（`folders` 可缺省为空数组）；
- `handleUpload` 改为调用 `props.onUpload(file)`，不再写本地 state；上传后清空 input value 的逻辑保留；
- `handleDelete` 改为调用 `props.onDeleteFile`；
- `handleRenameSubmit` 改为调用 `props.onRenameFile`；
- `handleMove` 改为调用 `props.onMoveFile`；
- 保留所有右键菜单、重命名输入、移动目标渲染等纯 UI 逻辑；
- 上传文件类型 fallback：未知扩展名不再回退到 `"PDF"`，改为回退到 `"TXT"`（满足 Edge case「未知扩展名作为通用文档」）。

### 6.4 `src/features/workspace/components/center/DocumentViewer.tsx`

- props 接收 `pendingFileName?: string`；
- 空状态文案「选择章节查看内容」/「点击左侧章节列表，解析内容将在此处展示」改为：
  - 初始空状态（无文件、无章节）：主文案「从左侧上传一份文档开始」；
  - 等待解析态（`pendingFileName` 有值）：主文案「`《pendingFileName》` 已上传，等待解析」，副文案「解析能力尚未接入，刷新后需要重新上传」；
- 其余逻辑不变。

### 6.5 `src/features/workspace/components/right/ChatPanel.tsx`

- 空状态文案「有什么可以帮你？」改为「上传一份文档后，我在这里帮你答疑」；
- 其余不变。

> 文案以本节为准；如有微调在实现阶段同步更新本 spec。

### 6.6 `src/features/workspace/components/left/SectionTree.tsx`

- 不改（已具备 `sections.length === 0` 的空状态「暂无章节数据 / 请先上传并解析文档」）。

## 7. 测试夹具策略

### 7.1 新增夹具文件

`src/features/workspace/__fixtures__/demoWorkspaceData.ts`，导出：

- `demoSections: SectionNode[]`（原 `getLocalizedSections()` 内容）；
- `demoContentBlocks: ContentBlock[]`（原 `getLocalizedContent()` 内容）；
- `demoFootnotes: FootnoteReference[]`（原 `initialFootnotes`）；
- `demoFiles: FileItem[]`（原 `getDefaultFiles("zh")` 内容）；
- `demoFolders: Folder[]`（原 `DEFAULT_FOLDERS`）。

夹具文件不放业务逻辑，纯数据导出，仅被测试 import。

### 7.2 `WorkspacePage.test.tsx` 改造

- 所有 `<WorkspacePage />` 渲染点改为 `<WorkspacePage initialFiles={demoFiles} initialSections={demoSections} initialContentBlocks={demoContentBlocks} initialFootnotes={demoFootnotes} />`，复用现有断言；
- 新增「空工作区」用例组（不传 initialXxx）：
  - 文件列表为空；
  - 章节树显示「暂无章节数据」；
  - 中栏显示「从左侧上传一份文档开始」；
  - 右栏显示新引导文案、不显示「有什么可以帮你？」；
- 新增「上传流程」用例组：
  - 触发上传 `lecture.pdf` → 列表出现、选中、切到章节树、中栏显示「`《lecture.pdf》` 已上传，等待解析」；
  - 上传取消（空 files）→ 状态保持空。

### 7.3 `FileManager.test.tsx` 改造

- 默认数据相关用例改为显式传入 `demoFiles` / `demoFolders`；
- 新增受控接口用例：
  - `onUpload` 在选择文件时被调用（参数为 `File` 对象）；
  - `onDeleteFile` / `onRenameFile` / `onMoveFile` 在右键操作时被调用；
  - 上传后 input value 被清空。

### 7.4 `ChatPanel.test.tsx` 改造

- 空状态断言改为「上传一份文档后，我在这里帮你答疑」。

### 7.5 `DocumentViewer.test.tsx` 改造

- 现有空状态用例文案更新为「从左侧上传一份文档开始」；
- 新增 `pendingFileName` 用例：传入 `pendingFileName="lecture.pdf"` → 显示等待解析态。

### 7.6 `SectionTree.test.tsx`

- 不改。

## 8. 数据流：上传主路径

```
用户点击「上传」按钮
  → FileManager 触发 <input type="file"> change
  → FileManager 调用 props.onUpload(file)
  → WorkspacePage.handleUpload(file):
      1. 构造 FileItem { id, name, type, size, date, status:"pending", category:"" }
      2. setFiles([newFile, ...files])
      3. setSelectedFileId(newFile.id)
      4. setSelectedFileName(newFile.name)
      5. setLeftMode("sections")
  → 渲染：
      左栏 SectionTree（空，显示「暂无章节数据」+ 返回按钮）
      中栏 DocumentViewer（pendingFileName 有值 → 「已上传，等待解析」）
      右栏 ChatPanel（空引导文案）
```

后续接入点：把 `handleUpload` 中的本地 `setFiles` 替换为 `documentApi.upload(file)` 调用，并在回填后写入 `files`。本任务不实现此步。

## 9. BDD 场景

```gherkin
Feature: Upload real study documents from an empty workspace

  Scenario: Empty workspace shows no demo placeholders
    Given the user opens the workspace
    Then the file list should be empty
    And the section tree should show "暂无章节数据"
    And the document viewer should show "从左侧上传一份文档开始"
    And the chat panel should show "上传一份文档后，我在这里帮你答疑"
    And "有什么可以帮你？" should NOT appear
    And "cours-analyse-s1.pdf" should NOT appear

  Scenario: User uploads a document from the file manager
    Given the user opens the empty workspace
    When the user chooses "lecture.pdf" from the upload button
    Then "lecture.pdf" should appear in the uncategorized area of the file list
    And "lecture.pdf" should be marked as selected
    And the left panel should switch to the section tree
    And the section tree should show "暂无章节数据"
    And the document viewer should show "《lecture.pdf》 已上传，等待解析"

  Scenario: Cancelling file selection keeps the workspace empty
    Given the user opens the empty workspace
    When the user cancels the upload file picker
    Then no file should be added to the list
    And the document viewer should remain showing "从左侧上传一份文档开始"

  Scenario: Unknown extension is treated as a generic document
    Given the user opens the empty workspace
    When the user chooses "notes.unknownext" from the upload button
    Then "notes.unknownext" should appear in the file list
    And the page should not crash
```

## 10. 文案定稿

| 位置 | 文案 |
| --- | --- |
| `ChatPanel` 空状态 | 上传一份文档后，我在这里帮你答疑 |
| `DocumentViewer` 初始空状态（无文件） | 从左侧上传一份文档开始 |
| `DocumentViewer` 等待解析态（已上传） | 《<文件名>》已上传，等待解析 |
| `SectionTree` 空状态（已具备） | 暂无章节数据 / 请先上传并解析文档 |

## 11. 验收标准

- AC1：初始进入工作区不显示任何演示文件、演示章节、演示解析内容或欢迎语「有什么可以帮你？」；
- AC2：左侧文件管理区显示空状态，存在「上传」按钮；
- AC3：点击「上传」可以选择本地文档文件（PDF/DOC/DOCX/PPT/PPTX/图片/TXT/MD）；
- AC4：选择文件后该文件出现在文件列表，并自动成为当前选中文档；
- AC5：选中文件后中栏显示「已上传，等待解析」，而非示例解析内容；
- AC6：上传逻辑在 `WorkspacePage.handleUpload` 处保留清晰接入点，后续可替换为 Python ingest API；
- AC7：取消文件选择时，工作区保持空状态；
- AC8：上传未知扩展名文件不导致页面崩溃。

## 12. 验证命令

- `npm run test:frontend`（必须通过，覆盖空状态 + 上传 + 受控接口 + 夹具复用）
- `npm run lint`（如有）
- `npm run build`（确保类型与构建无误）

## 13. 风险与备注

- 现有 `WorkspacePage.test.tsx` 与 `FileManager.test.tsx` 用例数量多，改造工作量集中在测试侧，生产代码改动相对集中；
- `FileManager` 受控化后，`folders` 保留三个默认文件夹（`课程资料/考试复习/论文参考`）作为空分类容器，让上传的未分类文件有归属感；这些文件夹本身不含演示文件，不违反 AC1；
- 本次不接后端，「等待解析」是会话内终态，刷新丢失，符合 Assumptions。

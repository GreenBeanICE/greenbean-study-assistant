# 原文面板设计方案

## 概述

在 DocumentViewer 中新增左右双栏布局，同时显示原文（原始文本）和解析（结构化内容），支持同步滚动和面板隐藏。

## 目标

- 用户可以同时查看原文和解析内容
- 支持同步滚动，方便对比
- 原文和解析面板都可以独立隐藏
- 复用现有 API 接口，无需新增后端接口

## 数据流

```
上传文件
    ↓
uploadDocument() → getDocumentDetail()
    ↓
detail.units (DocumentUnit[])
    ↓
┌─────────────────────────────────────────┐
│  原文面板：直接使用 units.text_content  │
│  解析面板：unitsToContentBlocks(units)  │
└─────────────────────────────────────────┘
    ↓
两个面板并排显示，共享同一份 units 数据
```

**关键点**：原文面板不需要新的 API 调用，直接复用 `getDocumentDetail` 返回的 `units` 数据。

## 组件结构

```
src/features/workspace/components/center/
├── DocumentViewer.tsx          (修改为双栏布局)
├── RawTextPanel.tsx            (新增：原文面板)
└── RawTextPanel.test.tsx       (新增：测试)
```

### 组件职责

| 组件 | 职责 |
|------|------|
| `DocumentViewer` | 容器组件，管理左右分栏布局和同步滚动 |
| `RawTextPanel` | 展示原始文本，按 DocumentUnit 分页/分单元显示 |

### RawTextPanel Props

```typescript
interface RawTextPanelProps {
  units: DocumentUnit[];           // 复用现有类型
  selectedUnitId?: string | null;  // 高亮当前选中的单元
  onUnitClick?: (unitId: string) => void;  // 点击单元回调
  viewerRef: React.RefObject<HTMLDivElement>;  // 同步滚动用
}
```

### DocumentViewer 新增 Props

```typescript
interface DocumentViewerProps {
  // ... 现有 props
  units: DocumentUnit[];           // 原始单元数据
  showRawPanel: boolean;           // 原文面板可见性
  showParsedPanel: boolean;        // 解析面板可见性
  onToggleRawPanel: () => void;    // 切换原文面板
  onToggleParsedPanel: () => void; // 切换解析面板
}
```

## 布局设计

### 默认布局（双栏并排）

```
┌─────────────────────────────────────────────────────────────┐
│ 顶部栏：文档解析                        [原文][解析][下载][分享] │
├─────────────────────────────────────────────────────────────┤
│ 工具栏                                                      │
├────────────────────────┬────────────────────────────────────┤
│      原文面板          │           解析面板                 │
│   (原始文本内容)       │        (结构化内容)                │
│   ┌──────────────┐     │     ┌──────────────────────┐       │
│   │ 第 1 页      │     │     │ 第 1 页              │       │
│   │ 原始文本...  │ ←───┼───→ │ • 标题               │       │
│   └──────────────┘     │     └──────────────────────┘       │
└────────────────────────┴────────────────────────────────────┘
```

### 隐藏状态组合

| 原文 | 解析 | 效果 |
|------|------|------|
| 显示 | 显示 | 双栏并排（默认） |
| 显示 | 隐藏 | 只看原文，解析宽度为 0 |
| 隐藏 | 显示 | 只看解析，原文宽度为 0 |
| 隐藏 | 隐藏 | 中间区域空白（不推荐，但允许） |

## 同步滚动实现

```typescript
const rawPanelRef = useRef<HTMLDivElement>(null);
const parsedPanelRef = useRef<HTMLDivElement>(null);
const isSyncingRef = useRef(false);

const handleRawScroll = () => {
  if (isSyncingRef.current) return;
  isSyncingRef.current = true;
  const ratio = rawPanelRef.current!.scrollTop / rawPanelRef.current!.scrollHeight;
  parsedPanelRef.current!.scrollTop = ratio * parsedPanelRef.current!.scrollHeight;
  isSyncingRef.current = false;
};

const handleParsedScroll = () => {
  if (isSyncingRef.current) return;
  isSyncingRef.current = true;
  const ratio = parsedPanelRef.current!.scrollTop / parsedPanelRef.current!.scrollHeight;
  rawPanelRef.current!.scrollTop = ratio * rawPanelRef.current!.scrollHeight;
  isSyncingRef.current = false;
};
```

## WorkspacePage 状态管理

### 新增状态

```typescript
const [showRawPanel, setShowRawPanel] = useState(true);
const [showParsedPanel, setShowParsedPanel] = useState(true);
const [documentUnitsByFileId, setDocumentUnitsByFileId] = useState<Record<string, DocumentUnit[]>>({});
```

### handleUpload 修改

在上传成功后缓存原始单元数据：

```typescript
setDocumentUnitsByFileId((prev) => ({
  ...prev,
  [fileId]: detail.units,
}));
```

### applyFileContent 修改

选择文件时加载对应的 units：

```typescript
const units = documentUnitsByFileId[fileId] ?? [];
```

## 测试策略

### RawTextPanel 测试

- 渲染空状态
- 渲染单元列表
- 高亮选中单元
- 点击回调
- 分页显示

### DocumentViewer 补充测试

- 双栏布局
- 隐藏原文
- 隐藏解析
- 同步滚动
- 按钮切换

### WorkspacePage 补充测试

- 上传后缓存 units
- 切换文件加载 units
- 面板状态切换

## 实现顺序

1. 新增 `RawTextPanel` 组件和测试
2. 修改 `DocumentViewer` 支持双栏布局
3. 修改 `WorkspacePage` 添加状态管理
4. 补充测试用例
5. 运行全量测试验证

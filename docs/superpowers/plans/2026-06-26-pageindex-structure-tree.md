# PageIndex Structure Tree Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把当前按页生成的伪 PageIndex 改成真实文档结构树，并让前端按结构树浏览与加载章节原文。

**Architecture:** 后端继续复用 `Section` 作为 PageIndex 节点语义，但 builder 不再按 `DocumentUnit` 一页一节点，而是先从解析元数据里抽取 heading/slide/paragraph 结构，再生成带真实父子关系的树节点和 `SectionUnitLink` 关联。前端继续使用现有 section API，但要补充树节点定位信息和节点文案展示，让左侧大纲与右侧原文加载都围绕统一 `section_id` 运行。

**Tech Stack:** Python 3.12、pytest、FastAPI、SQLAlchemy、React 19、TypeScript、Vitest、Testing Library

---

## File Map

- `backend-python/app/rag/page_index_builder.py`
  - 重写 builder，输出结构节点和节点到 `DocumentUnit` 的关联关系，而不是一页一个 `Section`。
- `backend-python/app/services/section_service.py`
  - 编排构树、脏数据检测、惰性重建、树查询和章节内容查询。
- `backend-python/app/repositories/section_repository.py`
  - 增加删除文档下所有 sections 的能力，支撑惰性重建。
- `backend-python/app/repositories/section_unit_link_repository.py`
  - 增加按文档或 section 删除 link 的能力，支撑惰性重建。
- `backend-python/app/repositories/document_unit_repository.py`
  - 继续复用 `list_by_document()` / `list_by_ids()`，必要时只补注释或排序测试，不大改实现。
- `backend-python/app/schemas/section_schema.py`
  - 扩展树节点响应，暴露 `start_page` / `end_page` 和可选定位文案字段。
- `backend-python/app/api/section_controller.py`
  - 保持接口路径不变，返回增强后的树节点和 build 结果。
- `backend-python/tests/unit/rag/test_page_index_builder.py`
  - 用真实结构树规则重写单测，覆盖 PDF/PPT/Word/fallback/空文档。
- `backend-python/tests/unit/services/test_section_service.py`
  - 增加惰性重建、多 unit 关联、内容读取优先级测试。
- `src/types/section.ts`
  - 扩展 `SectionNode`，加入页码/slide 展示所需字段。
- `src/features/section/api/sectionApi.ts`
  - 映射新的树节点响应结构。
- `src/features/section/api/sectionApi.test.ts`
  - 调整为结构树场景断言，不再固化 `Page 1`。
- `src/features/workspace/components/left/SectionTree.tsx`
  - 渲染节点标题与页码/slide 信息，保留展开折叠与高亮。
- `src/features/workspace/pages/WorkspacePage.tsx`
  - 确保首次进入文档、切换章节、恢复历史文档时都以结构树第一节点为默认节点，并对空节点提示保持正确。
- `src/features/workspace/pages/WorkspacePage.test.tsx`
  - 更新章节加载、切换和树渲染测试。
- `src/features/workspace/components/center/DocumentViewer.test.tsx`
  - 补充“空节点显示未找到内容”以及章节切换后的原文加载断言。

### Task 1: 重定义 Builder 输出契约并用测试锁定结构树行为

**Files:**
- Modify: `backend-python/app/rag/page_index_builder.py`
- Modify: `backend-python/tests/unit/rag/test_page_index_builder.py`

- [ ] **Step 1: 写失败测试，锁定结构树输出契约**

```python
from app.entities import DocumentUnit
from app.rag.page_index_builder import build_sections_from_units


def test_build_sections_creates_tree_from_heading_levels() -> None:
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=1,
            text_content="第一章\n引言",
            metadata_json={
                "source_type": "pdf",
                "headings": [{"title": "第一章", "level": 1}],
            },
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=1,
            page_number=2,
            text_content="1.1 背景\n内容",
            metadata_json={
                "source_type": "pdf",
                "headings": [{"title": "1.1 背景", "level": 2}],
            },
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=2,
            page_number=3,
            text_content="继续背景内容",
            metadata_json={"source_type": "pdf", "headings": []},
        ),
    ]

    result = build_sections_from_units("doc-1", units)

    assert [section.title for section in result.sections] == ["第一章", "1.1 背景"]
    assert result.sections[0].parent_section_id is None
    assert result.sections[1].parent_section_id == result.sections[0].id
    assert result.sections[0].start_page == 1
    assert result.sections[0].end_page == 3
    assert result.sections[1].start_page == 2
    assert result.sections[1].end_page == 3
    assert result.section_unit_links[result.sections[0].id] == [units[0].id, units[1].id, units[2].id]
    assert result.section_unit_links[result.sections[1].id] == [units[1].id, units[2].id]


def test_build_sections_falls_back_to_page_nodes_for_plain_pdf() -> None:
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=5,
            text_content="Plain page",
            metadata_json={"source_type": "pdf", "headings": []},
        )
    ]

    result = build_sections_from_units("doc-1", units)

    assert [section.title for section in result.sections] == ["第 5 页"]
    assert result.sections[0].metadata_json["fallback_kind"] == "page"


def test_build_sections_uses_slide_title_for_ppt_nodes() -> None:
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=1,
            text_content="课程概览",
            metadata_json={
                "source_type": "ppt",
                "headings": [{"text": "课程概览", "level": 1}],
            },
        )
    ]

    result = build_sections_from_units("doc-1", units)

    assert result.sections[0].title == "课程概览"
    assert result.sections[0].metadata_json["source_type"] == "ppt"
    assert result.sections[0].metadata_json["node_kind"] == "slide"


def test_build_sections_returns_empty_for_empty_units() -> None:
    result = build_sections_from_units("doc-1", [])

    assert result.sections == []
    assert result.section_unit_links == {}
```

- [ ] **Step 2: 跑 builder 测试，确认当前实现失败**

Run: `npm run test:python -- tests/unit/rag/test_page_index_builder.py -v`
Expected: FAIL，提示 `build_sections_from_units()` 仍返回 `list[Section]`，且没有父子关系、范围归并和多 unit 关联。

- [ ] **Step 3: 以最小实现重写 builder**

```python
from dataclasses import dataclass, field

from app.entities import DocumentUnit, Section


@dataclass
class SectionBuildResult:
    sections: list[Section] = field(default_factory=list)
    section_unit_links: dict[str, list[str]] = field(default_factory=dict)


def build_sections_from_units(document_id: str, units: list[DocumentUnit]) -> SectionBuildResult:
    if not units:
        return SectionBuildResult()

    sections: list[Section] = []
    section_unit_links: dict[str, list[str]] = {}
    level_stack: list[Section] = []
    active_sections: list[Section] = []

    for unit in units:
        headings = _normalize_headings(unit)
        if headings:
            created_for_unit = _create_sections_for_headings(document_id, unit, headings, sections, level_stack)
            active_sections = created_for_unit or active_sections
        elif not active_sections:
            fallback_section = _create_fallback_section(document_id, unit, len(sections))
            sections.append(fallback_section)
            level_stack[:] = [fallback_section]
            active_sections = [fallback_section]

        for section in active_sections:
            _extend_section_range(section, unit.page_number)
            section_unit_links.setdefault(section.id, []).append(unit.id)

    return SectionBuildResult(sections=sections, section_unit_links=section_unit_links)
```

- [ ] **Step 4: 再跑 builder 测试，确认通过**

Run: `npm run test:python -- tests/unit/rag/test_page_index_builder.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend-python/app/rag/page_index_builder.py backend-python/tests/unit/rag/test_page_index_builder.py
git commit -m "feat: build pageindex structure tree"
```

### Task 2: 让 SectionService 支持多 unit 关联和旧页级结构惰性重建

**Files:**
- Modify: `backend-python/app/services/section_service.py`
- Modify: `backend-python/app/repositories/section_repository.py`
- Modify: `backend-python/app/repositories/section_unit_link_repository.py`
- Modify: `backend-python/tests/unit/services/test_section_service.py`

- [ ] **Step 1: 写失败测试，覆盖惰性重建与 link 优先读取**

```python
def test_build_sections_rebuilds_legacy_page_nodes(uow_factory) -> None:
    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit = DocumentUnit(
        document_id=document.id,
        sequence_index=0,
        page_number=1,
        text_content="第一章",
        metadata_json={"source_type": "pdf", "headings": [{"title": "第一章", "level": 1}]},
    )
    legacy = Section(document_id=document.id, title="Page 1", level=1, order_index=0)

    with uow_factory() as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(unit)
        SectionRepository(uow.session).save(legacy)
        SectionUnitLinkRepository(uow.session).save(
            SectionUnitLink(section_id=legacy.id, document_unit_id=unit.id, order_index=0)
        )
        uow.commit()

    service = SectionService(uow_factory=uow_factory)
    sections = service.build_sections(document.id)

    assert [section.title for section in sections] == ["第一章"]
    assert sections[0].id != legacy.id


def test_get_section_content_prefers_section_links_over_page_range(uow_factory) -> None:
    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit_a = DocumentUnit(document_id=document.id, sequence_index=0, page_number=1, text_content="A")
    unit_b = DocumentUnit(document_id=document.id, sequence_index=1, page_number=2, text_content="B")
    section = Section(document_id=document.id, title="第一章", level=1, order_index=0, start_page=1, end_page=2)

    with uow_factory() as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(unit_a)
        DocumentUnitRepository(uow.session).save(unit_b)
        SectionRepository(uow.session).save(section)
        SectionUnitLinkRepository(uow.session).save(
            SectionUnitLink(section_id=section.id, document_unit_id=unit_b.id, order_index=0)
        )
        uow.commit()

    service = SectionService(uow_factory=uow_factory)
    content = service.get_section_content(section.id)

    assert [unit.text_content for unit in content] == ["B"]
```

- [ ] **Step 2: 跑 service 测试，确认当前实现失败**

Run: `npm run test:python -- tests/unit/services/test_section_service.py -v`
Expected: FAIL，提示旧页级结构没有被重建，且 service 仍按 `zip(sections, units)` 保存关联。

- [ ] **Step 3: 最小实现惰性重建与 link 持久化**

```python
class SectionService:
    def build_sections(self, document_id: str) -> list[Section]:
        with self.uow_factory() as uow:
            section_repo = SectionRepository(uow.session)
            link_repo = SectionUnitLinkRepository(uow.session)
            unit_repo = DocumentUnitRepository(uow.session)

            existing = section_repo.list_by_document(document_id)
            if existing and not self._is_legacy_page_sections(existing, link_repo):
                return existing

            if existing:
                link_repo.delete_by_document(document_id)
                section_repo.delete_by_document(document_id)

            units = unit_repo.list_by_document(document_id)
            build_result = build_sections_from_units(document_id, units)

            for section in build_result.sections:
                section_repo.save(section)
                for order_index, unit_id in enumerate(build_result.section_unit_links.get(section.id, [])):
                    link_repo.save(
                        SectionUnitLink(
                            section_id=section.id,
                            document_unit_id=unit_id,
                            order_index=order_index,
                        )
                    )

            uow.commit()
            return build_result.sections
```

- [ ] **Step 4: 再跑 service 测试，确认通过**

Run: `npm run test:python -- tests/unit/services/test_section_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend-python/app/services/section_service.py backend-python/app/repositories/section_repository.py backend-python/app/repositories/section_unit_link_repository.py backend-python/tests/unit/services/test_section_service.py
git commit -m "feat: rebuild legacy pageindex sections"
```

### Task 3: 扩展 section API 响应为结构树定位信息

**Files:**
- Modify: `backend-python/app/schemas/section_schema.py`
- Modify: `backend-python/app/api/section_controller.py`
- Create: `backend-python/tests/integration/api/test_section_controller.py`

- [ ] **Step 1: 写失败测试，锁定树节点响应字段**

```python
def test_get_section_tree_returns_page_range_fields(client, section_service_mock) -> None:
    root = SectionTreeNode(
        id="sec-1",
        title="第一章",
        level=1,
        order_index=0,
        start_page=1,
        end_page=3,
        children=[],
    )
    section_service_mock.get_section_tree.return_value = [root]

    response = client.get("/api/sections/documents/doc-1/tree")

    assert response.status_code == 200
    payload = response.json()["data"][0]
    assert payload["start_page"] == 1
    assert payload["end_page"] == 3
```

- [ ] **Step 2: 跑 API 测试，确认当前实现失败**

Run: `npm run test:python -- tests/integration/api/test_section_controller.py -v`
Expected: FAIL，提示 `SectionTreeNodeResponse` 不包含 `start_page` / `end_page`。

- [ ] **Step 3: 最小实现 schema 与 controller 响应扩展**

```python
class SectionTreeNodeResponse(BaseModel):
    id: str
    title: str
    level: int
    order_index: int
    start_page: int | None = None
    end_page: int | None = None
    children: list["SectionTreeNodeResponse"] = Field(default_factory=list)

    @classmethod
    def from_node(cls, node: SectionTreeNode) -> "SectionTreeNodeResponse":
        return cls(
            id=node.id,
            title=node.title,
            level=node.level,
            order_index=node.order_index,
            start_page=node.start_page,
            end_page=node.end_page,
            children=[cls.from_node(child) for child in node.children],
        )
```

- [ ] **Step 4: 再跑 API 测试，确认通过**

Run: `npm run test:python -- tests/integration/api/test_section_controller.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend-python/app/schemas/section_schema.py backend-python/app/api/section_controller.py backend-python/tests/integration/api/test_section_controller.py
git commit -m "feat: expose section tree location fields"
```

### Task 4: 前端类型与 API 映射改成结构树节点而非页列表节点

**Files:**
- Modify: `src/types/section.ts`
- Modify: `src/features/section/api/sectionApi.ts`
- Modify: `src/features/section/api/sectionApi.test.ts`

- [ ] **Step 1: 写失败测试，锁定树节点字段映射**

```ts
it("getSectionTree maps page range metadata into frontend nodes", async () => {
  vi.mocked(request).mockResolvedValueOnce([
    {
      id: "s1",
      title: "第一章",
      level: 1,
      order_index: 0,
      start_page: 1,
      end_page: 3,
      children: [],
    },
  ]);

  const result = await getSectionTree("doc-1");

  expect(result).toEqual([
    {
      id: "s1",
      title: "第一章",
      index: "1",
      expanded: true,
      startPage: 1,
      endPage: 3,
      children: [],
    },
  ]);
});
```

- [ ] **Step 2: 跑前端 API 测试，确认当前实现失败**

Run: `npm run test:frontend -- src/features/section/api/sectionApi.test.ts`
Expected: FAIL，提示前端 `SectionNode` 与 `toSectionNode()` 没有映射 `startPage` / `endPage`。

- [ ] **Step 3: 最小实现类型与映射扩展**

```ts
export interface SectionNode {
  id: string;
  title: string;
  children?: SectionNode[];
  index?: string;
  expanded?: boolean;
  startPage?: number | null;
  endPage?: number | null;
}

function toSectionNode(node: SectionTreeNodeResponse, parentIndex?: string): SectionNode {
  const index = parentIndex ? `${parentIndex}.${node.order_index + 1}` : `${node.order_index + 1}`;

  return {
    id: node.id,
    title: node.title,
    index,
    expanded: true,
    startPage: node.start_page,
    endPage: node.end_page,
    children: node.children?.map((child) => toSectionNode(child, index)),
  };
}
```

- [ ] **Step 4: 再跑前端 API 测试，确认通过**

Run: `npm run test:frontend -- src/features/section/api/sectionApi.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/types/section.ts src/features/section/api/sectionApi.ts src/features/section/api/sectionApi.test.ts
git commit -m "feat: map section tree metadata"
```

### Task 5: 左侧章节树渲染真实大纲节点信息

**Files:**
- Modify: `src/features/workspace/components/left/SectionTree.tsx`
- Modify: `src/features/workspace/components/left/SectionTree.test.tsx`

- [ ] **Step 1: 写失败测试，锁定节点文案不是纯页列表**

```ts
it("renders structure title with page range metadata", () => {
  render(
    <SectionTree
      sections={[
        { id: "sec-1", title: "第一章", index: "1", startPage: 1, endPage: 3, expanded: true },
      ]}
      selectedSectionId={null}
      onSelect={vi.fn()}
      onToggle={vi.fn()}
    />,
  );

  expect(screen.getByText("1 第一章")).toBeDefined();
  expect(screen.getByText("1-3 页")).toBeDefined();
  expect(screen.queryByText("Page 1")).toBeNull();
});
```

- [ ] **Step 2: 跑章节树测试，确认当前实现失败**

Run: `npm run test:frontend -- src/features/workspace/components/left/SectionTree.test.tsx`
Expected: FAIL，提示组件未渲染页码范围文案。

- [ ] **Step 3: 最小实现节点副标题显示**

```tsx
function formatSectionLocation(node: SectionNode): string | null {
  if (node.startPage == null && node.endPage == null) {
    return null;
  }
  if (node.startPage != null && node.endPage != null && node.startPage !== node.endPage) {
    return `${node.startPage}-${node.endPage} 页`;
  }
  const singlePage = node.startPage ?? node.endPage;
  return singlePage != null ? `第 ${singlePage} 页` : null;
}
```

- [ ] **Step 4: 再跑章节树测试，确认通过**

Run: `npm run test:frontend -- src/features/workspace/components/left/SectionTree.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/features/workspace/components/left/SectionTree.tsx src/features/workspace/components/left/SectionTree.test.tsx
git commit -m "feat: show structure tree locations"
```

### Task 6: Workspace 页面按结构树默认节点和章节切换加载原文

**Files:**
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`
- Modify: `src/features/workspace/pages/WorkspacePage.test.tsx`
- Modify: `src/features/workspace/components/center/DocumentViewer.test.tsx`

- [ ] **Step 1: 写失败测试，锁定首次加载和切换章节后的行为**

```ts
it("loads the first structure node content after building the section tree", async () => {
  (uploadDocument as Mock).mockResolvedValue({ id: "doc-1" });
  (getDocumentDetail as Mock).mockResolvedValue({ document: { id: "doc-1" }, units: [] });
  (buildSections as Mock).mockResolvedValue([]);
  (getSectionTree as Mock).mockResolvedValue([
    { id: "sec-1", title: "第一章", index: "1", expanded: true, startPage: 1, endPage: 2, children: [] },
  ]);
  (getSectionContent as Mock).mockResolvedValue([
    { id: "u-1", sequence_index: 0, page_number: 1, text_content: "第一章正文" },
  ]);

  render(<WorkspacePage />);
  await uploadPdf("lecture.pdf");

  await waitFor(() => {
    expect(getSectionContent).toHaveBeenCalledWith("sec-1");
  });
  expect(await screen.findByText("第一章正文")).toBeDefined();
});


it("shows missing-section-content hint when selected section has no units", () => {
  render(
    <DocumentViewer
      contentBlocks={[]}
      selectedSectionId="sec-1"
      viewerStatus="ready"
      footnotes={[]}
      expandedFootnoteId={null}
      showSelectionMenu={false}
      selectionMenuPos={null}
      onUpdateLineText={vi.fn()}
      onToggleFootnote={vi.fn()}
      onShowSelectionMenu={vi.fn()}
      onQuoteSelection={vi.fn()}
      units={[]}
    />,
  );

  expect(screen.getByText("未找到该小节内容")).toBeDefined();
});
```

- [ ] **Step 2: 跑页面与 viewer 测试，确认当前实现失败**

Run: `npm run test:frontend -- src/features/workspace/pages/WorkspacePage.test.tsx src/features/workspace/components/center/DocumentViewer.test.tsx`
Expected: FAIL，提示当前空内容文案仍是“该章节暂无解析内容”或首次节点加载流程未按结构树断言覆盖。

- [ ] **Step 3: 最小实现页面和 viewer 行为修正**

```tsx
const firstSectionId = sections[0]?.id ?? null;
dispatch({ type: "SELECT_SECTION", sectionId: firstSectionId });

if (firstSectionId) {
  const contentUnits = await getSectionContent(firstSectionId);
  setVisibleUnitsByFileId((prev) => ({ ...prev, [fileId]: contentUnits }));
}
```

```tsx
if (selectedSectionId && viewerStatus === "ready" && (units?.length ?? 0) === 0 && contentBlocks.length === 0) {
  return <p>未找到该小节内容</p>;
}
```

- [ ] **Step 4: 再跑页面与 viewer 测试，确认通过**

Run: `npm run test:frontend -- src/features/workspace/pages/WorkspacePage.test.tsx src/features/workspace/components/center/DocumentViewer.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/features/workspace/pages/WorkspacePage.tsx src/features/workspace/pages/WorkspacePage.test.tsx src/features/workspace/components/center/DocumentViewer.test.tsx
git commit -m "feat: drive viewer by structure tree sections"
```

### Task 7: 全量验证 PageIndex 结构树主链路

**Files:**
- Modify: `docs/superpowers/specs/2026-06-26-pageindex-structure-tree-design.md`
- Modify: `docs/superpowers/plans/2026-06-26-pageindex-structure-tree.md`

- [ ] **Step 1: 运行后端相关测试**

Run: `npm run test:python -- tests/unit/rag/test_page_index_builder.py tests/unit/services/test_section_service.py tests/integration/api/test_section_controller.py -v`
Expected: PASS

- [ ] **Step 2: 运行前端相关测试**

Run: `npm run test:frontend -- src/features/section/api/sectionApi.test.ts src/features/workspace/components/left/SectionTree.test.tsx src/features/workspace/pages/WorkspacePage.test.tsx src/features/workspace/components/center/DocumentViewer.test.tsx`
Expected: PASS

- [ ] **Step 3: 运行针对性回归测试**

Run: `npm run test:python -- tests/unit/services/test_document_ingest_service.py -v`
Expected: PASS，确认文档导入仍保留原有 `DocumentUnit` / `page_index_preview` 契约。

- [ ] **Step 4: 更新 spec/plan 中的验证备注（如有实际差异）**

```md
- Verification completed on 2026-06-26.
- Builder, service, API, tree rendering, workspace loading, and viewer empty-state tests pass.
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-06-26-pageindex-structure-tree-design.md docs/superpowers/plans/2026-06-26-pageindex-structure-tree.md
git commit -m "docs: record pageindex structure tree verification"
```

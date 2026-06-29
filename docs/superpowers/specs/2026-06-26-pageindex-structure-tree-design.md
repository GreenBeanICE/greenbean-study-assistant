# PageIndex Structure Tree Design

## 背景

- 当前实现把 `PageIndex` 简化成了按 `DocumentUnit` 逐页生成的平铺 `Section` 列表，左侧大纲因此显示为 `Page N` / `Unit N`。
- 这一实现不符合 US-04 / US-05 / US-06 的核心要求：`PageIndex` 应是文档结构索引树，页码或 slide 编号只是定位信息，不是树本身。
- 当前错误同时存在于 builder、service、测试和前端展示路径中，因此需要后端模型与前端行为一起修正。

## 目标

- 将 `PageIndex` 恢复为真实文档结构树。
- 让左侧面板按章节、标题、小节展示，而不是按页展示。
- 让右侧原文、已有解析和问答会话围绕统一的 `section_id` 对齐加载。
- 保留页码 / slide 编号作为节点定位信息，用于显示和原文范围查询。

## 非目标

- 不重做 `DocumentUnit` 的物理存储模型。
- 不在本次引入新的独立 `page_index_nodes` 实体；继续使用现有 `Section` 承担 PageIndex 树语义。
- 不在本次完成完整 AI 解析生成链路；若 `analyses` / `chat_sessions` 尚未完全接好，则返回明确空态。
- 不做大范围历史数据迁移脚本；只做按文档惰性重建。

## 当前问题

### 错误建模

- `backend-python/app/rag/page_index_builder.py` 当前按 `DocumentUnit` 一对一生成 `Section`，标题优先取单页 `headings[0]`，否则回退为 `Page N` 或 `Unit N`。
- `backend-python/app/services/section_service.py` 当前使用 `zip(sections, units)` 持久化 `SectionUnitLink`，等价于把“一个结构节点只关联一个原文单元”写死。
- 现有测试也把按页 fallback 的错误行为固化为正确结果。

### 用户可见后果

- 左侧大纲不是章节树，只是页列表。
- 章节切换与原文内容、解析结果、问答记录缺少统一的结构节点锚点。
- 后续 RAG、章节级解析和章节级问答都无法稳定绑定真实文档结构。

## 核心设计

### 数据职责

#### `DocumentUnit`

- 继续作为原文物理单元。
- PDF 通常是一页一个单元，PPT 通常是一张 slide 一个单元，Word/Text/Image 可按解析器输出保留现有单元策略。
- `DocumentUnit` 只负责原文持久化和基础元数据，不承担大纲语义。

#### `Section`

- 继续承担当前项目中的 PageIndex 节点角色，但语义更正为“结构节点”。
- 字段语义如下：
  - `title`：章节或节点标题。
  - `level`：标题层级。
  - `parent_section_id`：真实父节点。
  - `order_index`：按原文顺序的稳定排序值。
  - `start_page` / `end_page`：节点覆盖的页码或 slide 范围，仅用于定位与显示。
  - `metadata_json`：补充结构来源信息，例如 `source_type`、`slide_number`、`fallback_kind`、`text_range`、`node_kind`。

#### `SectionUnitLink`

- 从“补充关联”提升为“核心关联”。
- 一个 `Section` 可以关联多个 `DocumentUnit`，并通过 `order_index` 保存原文顺序。
- `get_section_content(section_id)` 优先依赖此关联取回完整原文，避免只靠页码猜测内容边界。

## 构树规则

### 总体原则

- 构树输入仍然是解析后的 `DocumentUnit` 集合。
- 先抽取结构信号，再生成树，不能再按 unit 直接一页一节点。
- 页码和 slide 编号是结构节点上的元数据，不是节点划分的第一原则。

### 标题优先

- 如果 `DocumentUnit.metadata_json.headings` 存在，则优先按 `heading.level` 建立树。
- 同一结构节点可以跨多个 `DocumentUnit` 持续覆盖；后续 unit 没有出现新标题时，归并到当前有效节点。
- 如果一个 unit 中存在多个 heading，则按其在原文中的顺序生成多个结构节点；每个新节点根据 `level` 决定其父节点。

### 格式特化规则

#### PDF

- 有明显标题层级时，按标题建树。
- 没有明显标题时，按页生成默认节点，标题格式为 `第 N 页`。
- 如果页级标题也无法构成稳定结构，但存在明显段落分隔，则允许按连续段落生成默认节点，标题格式为 `第 N 段`。

#### PPT / PPTX

- 优先按 slide 生成一级节点。
- 如果 slide 内可识别标题层级，则在该 slide 节点下继续挂子节点。
- 默认标题格式为 `第 N 张幻灯片`。

#### Word / DOCX

- 优先使用 heading 样式或解析结果中的标题层级建树。
- 没有可用 heading 时，再按段落或整文档 fallback。

#### Text / Image OCR

- 优先使用解析器提供的 heading / paragraph 结构信息。
- 如果没有结构信号，则按段落或整体生成默认节点。

### 空文档

- 空文档不生成伪结构树。
- builder 返回空结果，并由调用方转成“无法建立索引”的明确提示。

## 节点范围与内容关联

### 范围计算

- 节点首次出现所在的页码 / slide 记为 `start_page`。
- 节点及其子树结束前最后覆盖到的页码 / slide 记为 `end_page`。
- 对于无页码文档，可允许 `start_page` / `end_page` 为空，但仍通过 `SectionUnitLink` 保证可取回原文。

### 原文关联

- 每个结构节点都需要持久化对应的 `SectionUnitLink` 集合。
- 一个节点可关联多个 `DocumentUnit`。
- 关联顺序必须和原文阅读顺序一致。
- `get_section_content(section_id)` 先按 link 取内容；只有旧脏数据没有 link 时，才 fallback 到 `start_page/end_page` 范围查询。

## 后端行为

### `build_sections(document_id)`

- 首次打开文档时构建结构树并持久化。
- 如果数据库中已存在该文档的结构树，直接返回，不重复生成。
- 如果检测到历史脏数据仍是旧的页级 `Section`，触发该文档的惰性重建。

### 历史脏数据识别

- 满足以下特征时判定为旧页级结构，可触发重建：
  - 节点标题全部为 `Page N` / `Unit N` 风格。
  - 不存在真实层级关系。
  - 一个 `Section` 只关联一个 `DocumentUnit`，且与 unit 顺序严格一一对应。
- 重建仅影响该文档的 `Section` 与 `SectionUnitLink`，不修改 `DocumentRecord` 和 `DocumentUnit`。

### `get_section_tree(document_id)`

- 返回真实树形结构供前端直接渲染。
- 节点至少包含：`id`、`title`、`level`、`order_index`、`start_page`、`end_page`、`children`。

### `get_section_content(section_id)`

- 优先按 `SectionUnitLink` 取回完整 `DocumentUnit` 列表。
- 若节点没有可用内容，返回明确空结果，由前端展示“未找到该小节内容”。

## 前端行为

### 左侧结构树

- 左侧面板显示真实文档结构树，不再显示纯 `Page N` / `Unit N` 列表。
- 每个节点显示 `title` 以及页码 / slide 信息。
- 节点支持展开、折叠和高亮。
- 大纲顺序按 `order_index` 和原文顺序稳定展示。

### 右侧内容区

- 用户点击结构节点后，右侧原文面板加载该节点关联的完整原文。
- 如果节点内容为空，显示“未找到该小节内容”。
- 切换节点时同步更新高亮状态和右侧内容。

### 切换节点时的联动加载

- 原文：按 `section_id` 对应的 `SectionUnitLink` / `DocumentUnit` 加载。
- 已有解析：按 `section_id` 查询 `analyses`。
- 会话列表与历史问答：按 `section_id` 查询 `chat_sessions` / `chat_messages`。
- 如果后两者当前实现尚未完整落地，则前端显示明确空态，不伪造内容。

## 测试策略

### Builder 单元测试

- 带标题 PDF：生成真实章节树。
- 无标题 PDF：按页码或段落 fallback。
- PPT：按 slide 生成节点，并在可识别时生成子结构。
- Word：按 heading 层级生成树。
- 空文档：返回空结果并可被上层转换为失败提示。

### Service 单元测试

- 正确保留 `parent_section_id` 和层级关系。
- 一个 `Section` 关联多个 `DocumentUnit`。
- `get_section_content()` 优先使用 `SectionUnitLink`，只在旧数据情况下 fallback 到页码范围。
- 旧页级结构检测后可触发重建。

### 前端测试

- 左侧渲染结构树而不是页列表。
- 点击节点后右侧原文随之切换。
- 选中节点高亮。
- 空节点时显示“未找到该小节内容”。

## 风险与约束

- 当前解析器输出的 `headings` 丰富度可能不足，因此 fallback 规则必须真实可用，不能依赖“理想标题提取”。
- 由于项目当前继续复用 `Section` 作为 PageIndex 节点语义，字段命名上仍带有章节色彩，但本次不新增并行实体，避免过度扩张。
- 历史文档惰性重建需要确保只影响目标文档，避免误删或误改其他数据。

## 实施结论

- 本次改造采用“后端模型 + 前端展示一起纠正”的方案。
- `PageIndex` 的第一原则改为“文档结构树优先”，页码 / slide 退回为定位元数据。
- 所有点击、加载、解析和问答联动都围绕统一的 `section_id` 对齐。

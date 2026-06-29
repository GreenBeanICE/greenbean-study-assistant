# PDF Structured PageIndex Design

## 背景

- 当前 PDF 解析链路只输出“按页纯文本”，没有输出足够的结构信号。
- `Section` 构建阶段只能根据 `metadata.headings` 是否存在做弱判断；当 PDF 没有显式 `headings` 时，会退化成错误的 fallback 行为。
- 现象上会出现整份 PDF 被压成一个 `第 1 页` 节点，或只能得到按页平铺的伪结构，无法稳定支持章节树、按章节跳原文、章节级分析和后续 RAG 对齐。
- Word 路径已经开始向“多 `DocumentUnit` + 结构化消费”演进，PDF 需要补齐同等级别的结构抽取能力。

## 目标

- 让 PDF 在进入 `PageIndex -> Section -> 原文锚点` 链路前，先具备可消费的结构化信息。
- 让普通课程讲义、需求文档、报告类 PDF 能稳定生成真实章节树，而不是错误页节点。
- 保持当前 `section -> anchor_unit_id + units` 前后端契约可继续使用，不在第一阶段强行推翻现有展示和存储模型。
- 为后续章节级解析、引用定位、RAG chunk 对齐、页内精确跳转预留稳定数据基础。

## 非目标

- 第一阶段不把 `DocumentUnit` 从“页级”直接重构成“block 级”或“段落级”。
- 第一阶段不引入 OCR、视觉模型、外部版面理解服务或重量级新依赖。
- 第一阶段不承诺对扫描件 PDF、纯图片 PDF、极端排版 PDF 达到和可编辑 Word 一样的结构精度。
- 第一阶段不新增独立 `page_index_nodes` 数据实体，继续复用 `Section` 作为结构树节点。
- 第一阶段不修改前端大交互模型；前端只消费更准确的 section 结果。

## 成功标准

- 对于含明显标题层级的 PDF，左侧树应显示真实标题节点，而不是单个 `第 1 页` 总节点。
- 对于没有可识别标题但排版正常的 PDF，至少退化为“逐页稳定节点”，而不是“单节点吞全文”。
- 点击某个 `section` 后，原文面板返回的 `anchor_unit_id` 对应正确页级 `DocumentUnit`。
- `start_page` / `end_page` 与 section 覆盖范围一致，不再出现“第 1 页覆盖 1-24 页全文”的错误。
- 现有 Word、多 unit、section content、前端原文滚动能力不被回归破坏。

## 用户视角期望

- 有章节结构的 PDF：看到章节树，点击后能跳到对应章节开始页。
- 无章节结构的 PDF：看到逐页树，而不是失真的伪章节。
- 原文跳转和章节树是一致的，用户不需要理解内部是按 `DocumentUnit` 还是按 block 存储。

## 当前根因

### 1. Parser 输出过弱

- `backend-python/app/parsers/pdf_parser.py` 当前只抽取每页纯文本。
- `metadata` 里只有 `source_type`、空的 `headings`、粗略 `paragraphs_count`，没有行块、字体、坐标、样式、页面区域等结构信息。

### 2. Builder 被迫做无依据推断

- `backend-python/app/rag/page_index_builder.py` 当前基于 `DocumentUnit.metadata_json.headings` 构树。
- 一旦 `headings` 为空，就只能 fallback。
- 当前 fallback 逻辑不区分“无标题但仍应逐页独立”的 PDF 和“无页概念的连续文档”，导致 plain PDF 被错误归并。

### 3. 数据模型能力没有被充分利用

- `DocumentUnit.raw_content_json` 和 `metadata_json` 实际可以承载结构化块信息，但 PDF 解析路径没有写入这些信号。
- `SectionUnitLink` 已支持一个 section 关联多个 unit，但上游结构错误时，这一能力也无法发挥价值。

## 方案概述

本方案采用“结构信息前移”的思路：

- 在 `PDFParser` 阶段完成页内 block 抽取、样式聚合和标题候选识别。
- 在 `page_index_builder` 阶段消费这些 richer metadata，统一构建 section 树。
- 在没有足够结构信号时，再降级到逐页 fallback；逐页 fallback 是最后兜底，而不是主路径。
- 第一阶段保持 `DocumentUnit=页` 不变，只增强每个 unit 携带的结构化信息。

## 总体架构

### 第一阶段的职责划分

#### `PDFParser`

- 输入：PDF 二进制。
- 输出：仍然是一页一个 page item，但每页除 `content` 外，还包含结构化 `blocks`、`page_stats`、`headings` 候选。
- 负责“页面级结构抽取”和“页内标题候选识别”。

#### `DocumentIngestService`

- 保持一页一个 `DocumentUnit`。
- 把 page item 里的结构化信息安全保存进 `metadata_json` 和 `raw_content_json`。
- 不在 ingest 阶段做最终章节树决策。

#### `page_index_builder`

- 输入：带结构化 metadata 的 `DocumentUnit` 列表。
- 负责“跨页统一决策”：标题层级归一、父子关系、范围扩展、fallback 切换。
- 产出：`SectionBuildResult`，包含结构树节点和 `section_unit_links`。

#### `SectionService`

- 保持现有持久化与查询职责。
- 消费新的 builder 结果，不再假定 PDF 只会有弱 fallback。

## 数据设计

### `DocumentUnit` 保持页级不变

- 第一阶段仍然是“每页一个 `DocumentUnit`”。
- 这样可以避免同时重做：
- 数据库存储语义
- 原文面板渲染逻辑
- `section -> anchor_unit_id + units` 契约
- 已存在的 Word 多 unit 路径

### `metadata_json` 扩展

每个 PDF unit 的 `metadata_json` 增加以下结构：

```json
{
  "source_type": "pdf",
  "headings": [
    {
      "title": "1. Introduction",
      "level": 1,
      "confidence": 0.93,
      "source_block_id": "b-1",
      "numbering_pattern": "decimal"
    }
  ],
  "page_stats": {
    "page_width": 595.0,
    "page_height": 842.0,
    "primary_font_size": 10.5,
    "max_font_size": 18.0,
    "top_margin_cutoff": 80.0,
    "bottom_margin_cutoff": 780.0
  }
}
```

### `raw_content_json` 扩展

每个 PDF unit 的 `raw_content_json` 至少包含：

```json
{
  "page_number": 1,
  "parser_name": "PDFParser",
  "parser_version": "2.0.0",
  "blocks": [
    {
      "id": "b-1",
      "text": "1. Introduction",
      "bbox": [72.0, 96.0, 300.0, 120.0],
      "font_size": 18.0,
      "font_name": "Helvetica-Bold",
      "is_bold": true,
      "line_count": 1,
      "is_top_region": true,
      "is_bottom_region": false,
      "sequence_index": 0
    }
  ]
}
```

说明：

- 第一阶段这些字段只要求服务端内部稳定使用，不要求前端直接消费。
- `parser_version` 升级为 `2.0.0`，用于区分结构化新解析结果与旧结果。

## PDFParser 设计

### 抽取方式

- 继续使用现有 `PyMuPDF`，避免第一阶段引入额外大依赖。
- 不再只调用 `page.get_text("text")`。
- 改为优先使用可提供版面信息的抽取形式，提取 span/line/block 粒度信息，再自行归一化。

### Block 归一原则

- 将同一视觉块内的行合并为一个 block。
- 清理纯空白 block。
- 过滤明显页眉页脚噪音时只做轻量规则，不做激进删除。
- 保留 block 的原始顺序，作为后续标题识别和锚点扩展的基础。

### 标题候选识别

第一阶段采用规则融合，不引入模型：

#### 视觉信号

- 字号明显大于本页主字号。
- 字体名带 `Bold` 或 span 权重表现为粗体。
- 单行或短文本块。
- 上下存在明显留白。

#### 文本信号

- 命中常见标题编号模式：
- `1`
- `1.1`
- `1.1.1`
- `Chapter 1`
- `Section 2`
- `第1章`
- `第1节`
- `一、`
- `（一）`
- 命中标题常见特征：短句、非完整长段落、末尾不以正文长句特征收尾。

#### 位置/区域信号

- 位于页面上半区更可信。
- 位于页眉/页脚区域更不可信。
- 位于段落起始附近更可信。

#### 一致性信号

- 同类字号/样式在多页重复出现时，提高该组样式的标题可信度。
- 若某一编号模式已在前文被采纳为标题，后续同模式候选置信度上调。

### 置信度与输出

- 每个 heading 候选都写出 `confidence`。
- 只有达到阈值的候选进入 `metadata.headings`。
- 阈值以下的候选保留在 block 数据中，但不进入正式 heading 列表。

### 空结构页处理

- 某一页没有识别出 heading 时，不代表该页没有内容。
- 后续 builder 可以把它归并到前一个有效 section，或者在全篇都无 heading 时转入逐页 fallback。

## Section 构建设计

### 核心原则

- builder 不再把“有没有 heading”当成唯一维度。
- builder 分两阶段：
- 全文扫描，归一 heading 候选序列
- 再根据归一结果构树与挂接 unit

### 构树流程

#### 阶段 1：扫描所有 units

- 读取每页 `metadata_json.headings`。
- 提取候选标题流，保留页号、原始顺序、level、confidence。

#### 阶段 2：层级归一

- 如果 level 明确且稳定，直接采用。
- 如果 level 缺失或冲突，结合编号深度推断：
- `1` -> level 1
- `1.1` -> level 2
- `1.1.1` -> level 3
- `一、` / `第1章` 一般视为 level 1
- `（一）` / `第1节` 视上下文决定 level 2 或 3
- 对异常跳级做温和修正，避免无父节点孤儿树。

#### 阶段 3：生成 section 树

- 遇到新 heading 时新建 `Section`。
- 使用 level stack 建立父子关系。
- 新节点 `start_page` 为首次命中页。
- 旧节点及祖先节点在后续 units 持续扩展 `end_page`。

#### 阶段 4：挂接 units

- 每个 unit 至少会被挂到一个 section。
- 如果该页开启了新 section，则挂到新 section 以及其祖先。
- 如果该页没有新 heading，则挂到当前活跃 section 及其祖先。

### 低置信度候选处理

- 低置信度候选不直接建 section。
- 避免把普通正文中的粗体句子误识别成章节。
- 当整篇只有少量低置信度候选且无法形成稳定树时，不勉强建章节，直接进入 fallback。

## Fallback 设计

### 触发条件

当全文扫描后满足以下任一条件时，进入 fallback：

- 没有任何通过阈值的 heading。
- 识别结果数量过少且无法形成稳定结构。
- 识别结果高度冲突，构树后明显劣于逐页浏览。

### Fallback 规则

#### PDF 第一优先 fallback：逐页节点

- 对有稳定 `page_number` 的 PDF，按页创建 fallback section。
- 标题格式为 `第 N 页`。
- 每页一个节点，不允许再把多页吞并进第一页节点。

#### 非 PDF 或无页码内容

- 保持现有 paragraph/document fallback 逻辑。
- 本 spec 不改变 Word/Text 的无页码 fallback 语义。

### 为什么逐页 fallback 必须保留

- 即使结构识别失败，逐页导航仍然比“单节点全文”更可用。
- 这是用户体验底线，也是调试结构抽取问题时的重要退路。

## `SectionUnitLink` 设计要求

- 每个 section 必须保存有序的 unit 关联。
- 任何 fallback section 也必须有完整 link，不依赖后查页码猜内容。
- `get_section_content(section_id)` 继续优先使用 `SectionUnitLink`。
- 只有历史旧数据没有 link 时，才允许使用 `start_page/end_page` 兜底查询。

## 历史数据与重建策略

### 新旧解析结果并存

- 已经入库的旧 PDF 文档可能仍然是 `parser_version=1.0.0` 风格。
- 新上传文档直接走结构化解析。

### 惰性重建

- 当用户打开旧 PDF 文档并触发 `build_sections(document_id)` 时：
- 若检测到是旧结构或旧 parser 结果，可触发该文档惰性重建 section。
- 第一阶段只重建 section 树，不强制重跑整份 PDF 解析。

### 是否重解析 PDF

- 第一阶段默认不自动批量重解析历史 PDF。
- 如果旧文档缺少结构化 block 数据，则可先落回稳健逐页 fallback。
- 后续若需要，再补“按需重解析单文档”能力。

## 前端影响

### 第一阶段前端原则

- 前端接口尽量不变。
- `WorkspacePage`、`DocumentViewer`、`RawTextPanel` 继续消费：
- section tree
- `anchor_unit_id`
- `units`

### 预期改善

- 章节树会从“一个错误总节点”变成“真实章节树或逐页树”。
- 原文跳转自然随之变准，不需要前端特殊补丁。

### 暂不做的前端增强

- 不新增 `anchor_block_id`。
- 不做页内标题高亮定位。
- 不改动当前解析面板空态逻辑。

## 分阶段实施

### Phase 1：结构化 PDF PageIndex

目标：先把 PDF 的 section 生成做对。

包含：

- `PDFParser` 输出 blocks、page stats、headings
- `DocumentIngestService` 保存新结构化数据
- `page_index_builder` 消费 richer metadata 构树
- `SectionService` 在旧数据场景下保持惰性重建可用
- 补齐 parser/builder/service/integration 测试

不包含：

- block 级锚点
- PDF 重解析后台任务
- OCR / 扫描件专项增强

### Phase 2：页内精确锚点

目标：从“跳到正确页”升级为“跳到正确标题块或段落”。

可能包含：

- section content 返回 `anchor_block_id`
- 前端原文面板对 block 级高亮和滚动支持
- analysis / quote / citation 对 block 粒度对齐

### Phase 3：复杂 PDF 增强

目标：提升扫描件、双栏、复杂排版、弱标题文档的结构识别率。

可能包含：

- OCR 路径
- 更强的版面理解
- 可配置规则或轻量模型

## 测试策略

### Parser 单元测试

- 能从简单 PDF 页提取结构化 blocks。
- 能识别明显字号更大且带编号的标题为 heading。
- 不把普通正文首句误识别成 heading。
- 页眉页脚文本默认不应高置信进入 heading。

### Builder 单元测试

- 多页 PDF 中，heading level 能构成父子树。
- 某页没有 heading 时，可正确继承到当前活跃 section。
- 全文无 heading 时，按页生成逐页 fallback sections。
- fallback 时每页独立，不再出现第一页吞并全文。

### Service 单元测试

- `get_section_content()` 对多 unit section 返回正确 `anchor_unit_id`。
- 旧 section 脏数据仍可惰性重建或安全 fallback。

### 集成测试

- 真实两页 PDF：无 heading 时生成两个逐页节点。
- 带明显标题层级的测试 PDF：生成真实 section 树。
- 上传后 `build_sections -> get_section_tree -> get_section_content` 全链路一致。

### 前端回归测试

- 无需新增大规模行为测试，只需验证现有 section 选择逻辑在新返回结果下仍成立。
- 如有必要，补一条“多 section PDF 返回正确 anchor”的页面级测试。

## 风险

### 误判风险

- 某些粗体正文或列表项可能被误识别为标题。
- 通过置信度阈值、样式一致性、编号模式和区域规则联合降低误判。

### 漏判风险

- 某些标题样式很弱，可能识别不出。
- 这类文档应退回逐页 fallback，而不是产出错误章节树。

### 历史数据差异

- 老文档没有结构化 block 数据时，第一阶段无法凭空恢复真实标题。
- 需要接受“旧文档可稳态逐页，新文档结构更强”的阶段性结果。

### 复杂度控制

- 如果第一阶段同时引入 block 级 `DocumentUnit`，复杂度会明显失控。
- 因此本方案明确延后这部分，只先增强 metadata。

## 为什么不直接把 `DocumentUnit` 改成 block 级

- 那会同时影响：
- 原文展示顺序
- 章节锚点契约
- 持久化语义
- 现有 Word 路径
- 后续 chunk / analysis / quote 相关测试
- 这不是不能做，而是不应该和本次“先把 PDF 章节树做对”耦合到一个迭代里。

## 验收标准

- 示例中的 24 页 PDF 不再显示为单个 `第 1 页 (1-24 页)` 节点。
- 对无结构 PDF，左侧最差也应展示 24 个逐页节点。
- 对有明显标题的 PDF，左侧应展示标题节点，且点击后原文跳转到正确页。
- `SectionUnitLink` 顺序与用户阅读顺序一致。
- 新增测试覆盖 parser、builder、service、integration 四层。

## 实施结论

- 这是一次中到偏大的后端结构增强，而不是前端补丁修复。
- 第一阶段通过“结构化 parser + 智能 builder + 稳健 fallback”解决根因。
- 它能在不推翻现有前后端契约的前提下，把 PDF 从“几乎没有结构语义”升级到“常见文档可稳定导航”的水平。

# 章节 AI 解析生成与展示设计

## 背景

当前工作区页面已经打通了以下链路：

- 上传文档并解析为 `DocumentUnit`
- 基于 `SectionService` 构建章节树
- 左侧选择章节后加载该章节原文
- 中间区域以 `DocumentViewer` 展示原文面板与“解析”面板

但“解析”面板仍停留在空占位状态：

- 前端 `WorkspacePage` 对每个文件的 `contentBlocks` 始终写入空数组
- 章节切换时不会查询任何 analysis 数据
- `DocumentViewer` 只会显示“暂无解析内容”或“该章节暂无解析内容”
- 后端 `analysis_controller.py` 仍是占位文件，未注册 analysis 路由

User Story v4.1 中的 US-08 要求：用户选择小节后，如果已有解析则直接展示；如果没有解析，用户可点击“生成解析”，系统基于当前小节原文生成结构化解析，并最终保存到 `analyses` 表中。

## 目标

- 补齐章节 AI 解析的后端 API，使前端可以查询或生成指定章节的解析
- 让前端在章节切换后优先尝试加载已有解析；若不存在，则提供“生成解析”入口
- 让生成成功的结果复用现有 `DocumentViewer` 的 `contentBlocks` 展示能力
- 按阶段推进：先打通 API，再打通前端交互与展示，最后补持久化与复用
- 保持 analysis 所使用的 provider 与现有 chat provider 一致，通过 `ProviderRegistry.get_active_chat()` 获取

## 非目标

- 不处理右侧 AI 助手或会话持久化
- 不改造 Tauri 桌面桥接层
- 不在本轮补完整的 Agent 路由逻辑
- 不额外引入新的前端状态库、服务总线或后端异步任务系统
- 不在本轮完成完整的“相邻兄弟节点 chunks 补充检索”实现

## 方案对比

### 方案一：后端返回领域 analysis，前端负责转换为 `contentBlocks`

- 后端返回 `AnalysisResponse`，保留 `content_json`、`content_markdown`、`source_refs` 等领域字段
- 前端新增一个轻量转换函数，将 analysis 结果映射为 `ContentBlock[]`
- `DocumentViewer` 继续使用现有渲染协议

优点：

- 保持前后端边界清晰
- 不让后端直接依赖前端展示结构
- 最符合当前仓库分层风格

缺点：

- 前端需要新增一层转换代码

### 方案二：后端直接返回前端专用 `contentBlocks`

- analysis API 直接返回 `ContentBlock[]`
- 前端直接写入状态并展示

优点：

- 前端接线最少

缺点：

- 后端与前端展示协议耦合过深
- 不利于后续复用 analysis 数据做持久化、导出或其他界面展示

### 方案三：前端先本地 mock“生成解析”按钮，后端后补

- 先实现按钮、加载态、错误态
- 后续再替换为真实 API

优点：

- 能较快看到交互外观

缺点：

- 与主人要求的优先级相反
- 很容易产生重复改动

推荐采用方案一。

## 设计决策

### 1. 分阶段实现策略

按主人确认的顺序分三段推进：

1. 先补“生成章节/全文 AI 解析”的后端 API
2. 再补前端点击“生成解析”时触发生成并展示 `contentBlocks`
3. 最后补 analyses 持久化，避免每次重新生成

其中“全文 AI 解析”本轮只在 API 设计上预留 `analysis_type` 和 schema，不在工作区界面中启用；工作区页面实际只接入“章节解析”。

### 2. 最小可用上下文策略

User Story v4.1 强调首次生成解析仅基于原文知识库，不参考任何生成内容。结合当前仓库状态，本轮采用如下最小可用实现：

- 上下文来源仅为当前章节的 `DocumentUnit` 原文
- 上下文中附带最小来源信息：页码、章节标题、原文顺序
- 不读取 `analysis_results` 或 `chat_messages` 作为生成上下文
- 不要求本轮接入 `chunks + sqlite-vec` 检索，也不补兄弟节点扩展检索

这样可以满足“仅基于原文”这一核心规则，同时避免把还未完成的 RAG 检索基础设施耦合进第一版章节解析。

后续如果要升级为“PageIndex + chunks + 相邻兄弟节点补充”，应保持 API contract 不变，仅替换 `AnalysisService` 的上下文构建策略。

### 3. 后端分层设计

后端新增和修改的职责边界如下：

- `app/api/analysis_controller.py`
  - 提供章节 analysis 查询与生成接口
  - 负责状态码、错误映射、响应 schema 序列化
- `app/api/dependencies.py`
  - 新增 `get_analysis_service()`
- `app/services/analysis_service.py`
  - 组织章节原文加载、上下文构建、调用 `AnalysisAgent`、构造 `AnalysisResult`
  - 提供“查询已有 section analysis”和“生成 section analysis”两个入口
- `app/services/section_service.py`
  - 补充 `get_section_by_id()`，供 analysis service 获取章节元信息
- `app/schemas/analysis_schema.py`
  - 补充 section analysis 响应、source refs 响应和必要的转换方法
- `app/repositories/analysis_result_repository.py`
  - 第三阶段补齐按 `section_id` / `document_id + analysis_type` 查询能力

`AnalysisAgent` 继续作为 LLM 调用边界，不直接耦合 HTTP 或数据库逻辑。

### 4. API 设计

新增两个章节 analysis 接口：

- `GET /api/analyses/sections/{section_id}`
- `POST /api/analyses/sections/{section_id}/generate`

返回形态统一沿用现有 `{ code, data, message? }` 包装。

#### `GET /api/analyses/sections/{section_id}`

职责：

- 第三阶段之前：可以先返回 404，明确表示当前章节尚无持久化解析
- 第三阶段之后：优先从 `analysis_results` 读取 `analysis_type = section` 且 `section_id = {section_id}` 的结果

返回体核心字段：

- `id`
- `document_id`
- `section_id`
- `analysis_type`
- `language`
- `content_markdown`
- `content_json`
- `source_refs`
- `created_at`
- `updated_at`

#### `POST /api/analyses/sections/{section_id}/generate`

职责：

- 根据 `section_id` 获取章节及其原文单元
- 仅基于原文构建 prompt context
- 调用 `AnalysisAgent` 使用现有 chat provider 生成结构化 JSON
- 构造成 `AnalysisResult`
- 第三阶段起持久化至 `analysis_results`
- 将 analysis 返回给前端

请求体建议最小化，避免过早设计全文解析参数：

- `language?: string`，默认 `zh`
- `force_regenerate?: boolean`，默认 `false`

其中：

- 第二阶段前，`force_regenerate` 可暂不使用
- 第三阶段后，当存在已持久化解析时，如果 `force_regenerate = false`，后端可以直接返回已有结果；若为 `true`，则重新生成并覆盖保存

### 5. 错误语义

章节 analysis 的错误语义保持可读、可重试：

- 章节不存在：404
- 章节存在但无可用原文：400，错误信息使用“资料依据不足”或等价表达
- 未激活 chat provider：400 或 409，错误信息明确提示先配置模型
- LLM 返回非法 JSON：502 或 500，提示“生成结果格式不正确，请重试”
- 数据库存取失败：500，提示“解析保存失败”

前端收到这些错误后不兜底伪造内容，只展示错误和重试按钮。

### 6. 前端数据与状态设计

前端在现有 `WorkspacePage` 内增加章节解析相关状态，不引入新的全局 store。

建议新增两类缓存：

- `sectionAnalysisByFileId: Record<string, Record<string, ContentBlock[]>>`
- `sectionAnalysisStatusByFileId: Record<string, Record<string, "idle" | "loading" | "ready" | "error">>`

必要时可再加：

- `sectionAnalysisErrorByFileId: Record<string, Record<string, string | null>>`

缓存 key 规则：

- 第一层 key：当前已收敛后的 `fileId`
- 第二层 key：`sectionId`

这样可避免在切换文档或章节时相互污染，也与当前 `documentUnitsByFileId`、`documentSectionsByFileId` 的缓存风格保持一致。

### 7. 前端交互设计

章节切换后的中间“解析”面板行为：

1. 用户点击章节
2. 系统继续像现在一样加载该章节原文
3. 同时尝试调用 `GET /api/analyses/sections/{section_id}`
4. 若返回已有解析，则将其转换为 `contentBlocks` 并展示
5. 若返回 404，则显示“生成解析”按钮，而不是只有空占位文案
6. 用户点击“生成解析”后调用 `POST /generate`
7. 进入加载态，按钮禁用并显示生成中状态
8. 成功后写入该章节缓存并展示
9. 失败后展示错误提示和重试按钮

### 8. `DocumentViewer` 的最小改造

`DocumentViewer` 继续负责展示，不承担 API 调用。建议补充以下能力：

- 支持新的解析空态类型：`no-analysis-yet`
- 在 `selectedSectionId` 存在、原文已加载但 `contentBlocks` 为空时，显示“生成解析”按钮
- 接收以下新增 props：
  - `analysisStatus?: "idle" | "loading" | "ready" | "error"`
  - `analysisErrorMessage?: string | null`
  - `onGenerateAnalysis?: () => void`

这样变更最小：

- 原文面板逻辑不动
- 现有 `contentBlocks` 渲染逻辑不动
- 仅扩展解析空态与按钮区域

### 9. analysis 到 `contentBlocks` 的映射

前端新增一个纯函数，例如：

- `src/features/analysis/analysisToContentBlocks.ts`

映射策略：

- `summary` -> 一个标题为“摘要”的文本块
- `key_concepts` -> 一个标题为“核心概念”的文本块，逐条映射为 paragraph/list line
- `terms` -> 一个标题为“中法术语”的表格块或逐条文本块
- `highlights` -> 一个标题为“重点提炼”的文本块
- `source_refs` -> 映射为 `FootnoteReference[]` 或先以普通来源文本追加在块尾

第一版优先目标是可展示和可编辑，因此允许先把所有分析内容映射为文本块；术语表格和可点击原文引用可留在后续增强。

### 10. 持久化设计

第三阶段接入 `analysis_results` 表，复用现有 `AnalysisResultModel` 与 `AnalysisResultRepository`。

需要补齐的 repository 能力：

- `get_by_section_id(section_id: str) -> AnalysisResult | None`
- `save(result: AnalysisResult)` 已存在，可直接复用

推荐持久化规则：

- `analysis_type = AnalysisType.SECTION`
- `section_id` 必填
- `document_id` 来自 `Section.document_id`
- `content_json` 保存 LLM 结构化结果
- `content_markdown` 保存由 `build_markdown_from_json()` 生成的展示文本
- `language` 默认 `zh`
- `prompt_version` 在本轮固定为一个显式值，例如 `section-v1`

保存后，下次同章节进入时直接读取，避免重新生成。

### 11. 测试设计

后端测试分三层：

- unit
  - `AnalysisService`：无原文时拒绝生成、生成成功时构造 `AnalysisResult`、已有解析命中时直接返回
- integration/api
  - analysis controller 的 GET/POST 正常返回与 404/400 错误语义
- repository/integration
  - `AnalysisResultRepository.get_by_section_id()` 可读回持久化记录

前端测试分两层：

- `WorkspacePage.test.tsx`
  - 选择章节后存在解析时自动展示
  - 选择章节后无解析时显示“生成解析”按钮
  - 点击生成后显示加载态并展示结果
  - 生成失败后显示错误和重试入口
- `DocumentViewer.test.tsx`
  - 在有原文、无解析、传入 `onGenerateAnalysis` 时显示按钮
  - 生成中和失败状态文案正确

## 影响范围

- 后端
  - `backend-python/app/api/analysis_controller.py`
  - `backend-python/app/api/dependencies.py`
  - `backend-python/app/main.py`
- `backend-python/app/services/analysis_service.py`
- `backend-python/app/services/section_service.py`
- `backend-python/app/schemas/analysis_schema.py`
- `backend-python/app/repositories/analysis_result_repository.py`
- 前端
  - `src/features/workspace/pages/WorkspacePage.tsx`
  - `src/features/workspace/components/center/DocumentViewer.tsx`
  - `src/features/workspace/type.ts`
  - `src/features/analysis/api/analysisApi.ts`
  - `src/features/analysis/analysisToContentBlocks.ts`
  - `src/types/analysis.ts`
- 测试
  - `backend-python/tests/unit/services/test_analysis_service.py`
  - `backend-python/tests/integration/api/test_analysis_controller.py`
  - `backend-python/tests/integration/persistence/test_sqlite_repositories.py` 或新增 analysis repository 测试文件
  - `src/features/workspace/pages/WorkspacePage.test.tsx`
  - `src/features/workspace/components/center/DocumentViewer.test.tsx`

## 验收标准

- 选择章节后，如果已有解析，则中间“解析”面板直接展示该结果
- 选择章节后，如果没有解析，则中间“解析”面板显示“生成解析”入口
- 点击“生成解析”后，系统仅基于当前章节原文调用 LLM 生成解析
- 生成成功后，结果以现有 `contentBlocks` 机制展示
- 生成失败后，前端显示明确错误并支持重试
- analysis 使用与 chat 相同的 provider 配置来源
- 第三阶段完成后，同一章节再次打开时优先读取已保存解析，不重复生成

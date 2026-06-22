# GreenBean Document And RAG Current-Framework Design

## 1. 背景与目标

本设计文档用于校准 `AI 学业助手 MVP v4.1 文档处理与 RAG 执行计划`，目标是在**完全沿用当前仓库框架、目录分层、实体命名和前端主工作区结构**的前提下，重新定义文档处理与 RAG 主链路。

本次设计只覆盖主链路闭环：

- 单文件上传
- 文档解析与原文单元持久化
- 章节结构生成与浏览
- 原文 Chunk 切分与检索
- 基于当前章节的 AI 解析
- 基于当前文档/章节上下文的继续追问

本次设计明确排除以下范围：

- provider 配置管理的完整产品化流程
- 导出能力
- 历史文档恢复的扩展场景
- 多工作区复杂切换
- Tauri 业务逻辑扩展

## 2. 当前项目真实基线

### 2.1 前端基线

- 当前真正的主交互壳是 `src/features/workspace/pages/WorkspacePage.tsx`，不是独立的 `document` / `analysis` / `chat` 页面流。
- `workspace` 已具备左中右三栏骨架：
  - 左栏文件管理：`src/features/workspace/components/left/FileManager.tsx`
  - 左栏章节树：`src/features/workspace/components/left/SectionTree.tsx`
  - 中栏原文查看：`src/features/workspace/components/center/DocumentViewer.tsx`
  - 右栏聊天面板：`src/features/workspace/components/right/ChatPanel.tsx`
- `src/features/document/api/`、`src/features/section/api/`、`src/features/analysis/api/`、`src/features/chat/api/` 目前基本是占位，更适合作为数据访问层，而不是承载主页面。

### 2.2 Python 后端基线

- `backend-python/app/main.py` 当前仅注册了文档上传路由，说明主链路应该在现有入口上逐步补齐，而不是重新设计第二套入口。
- `backend-python/app/services/document_ingest_service.py` 已能把 parser 输出转成 `DocumentRecord` 与 `DocumentUnit`，但当前仍偏向内存模式。
- `backend-python/app/services/section_service.py`、`chunk_service.py`、`chat_service.py` 仍为占位。
- `backend-python/app/services/analysis_service.py` 已有演示性质的分析实体组装代码，但尚未成为正式 service。
- `backend-python/app/rag/page_index_builder.py` 与 `retriever.py` 仍是占位骨架。

### 2.3 数据模型基线

- 当前数据模型已经围绕现有实体命名落地：
  - `DocumentRecord`
  - `DocumentUnit`
  - `Section`
  - `Chunk`
  - `AnalysisResult`
  - `ChatSession`
  - `ChatMessage`
- 数据库初始化和 ORM 也已经采用这套命名：
  - `document_records`
  - `document_units`
  - `sections`
  - `chunks`
  - `analysis_results`
  - `chat_sessions`
  - `chat_messages`
- 本设计不做实体名和表名迁移，不引入 v4.1 新命名表。

## 3. 设计原则

### 3.1 保持现有命名不变

即使 v4.1 原始设想采用 `documents/pages/page_index_nodes/analyses` 命名，本项目也继续使用现有实体和表名，以降低改造成本并保持与现有测试、仓库、ORM、Repository 的一致性。

### 3.2 语义对齐，结构不动

本次不是“理想化重构”，而是让当前框架中的实体承担 v4.1 主链路语义：

- `DocumentRecord` 承担文档主记录
- `DocumentUnit` 承担页面级或统一原文单元
- `Section` 承担 PageIndex/章节树语义
- `Chunk` 承担 RAG 检索片段
- `AnalysisResult` 承担章节解析结果
- `ChatSession` / `ChatMessage` 承担追问会话

### 3.3 前端主链路并入 workspace

所有主流程交互最终都并入 `workspace` 页面，不再规划第二条独立主页面流。

### 3.4 少量新增文件

只在现有目录结构中补充少量必需文件，例如缺失的 schema、mapper、workspace 数据访问辅助文件；不额外新建大批模块。

### 3.5 页面展示与检索职责分离

- 页面展示使用 `DocumentUnit + Section`
- RAG 检索使用 `Chunk`

这样既能贴合当前数据结构，也能避免用 chunk 反向拼接页面正文，减少展示误差。

## 4. 方案对比与推荐

### 4.1 方案 A：语义对齐、结构不动（推荐）

保留现有实体、目录、表名、前端主壳，通过 service 和 API 补全主链路能力。

优点：

- 与当前仓库最一致
- 不破坏已有 Repository、ORM、测试结构
- 前端可以直接接入 `workspace`
- 计划精度最高、实施阻力最低

缺点：

- 需要在文档中明确现有命名与 v4.1 语义映射

### 4.2 方案 B：前端优先串流程

先把 `workspace` 的上传、大纲、原文、右栏交互串起来，再逐步回填后端真实能力。

优点：

- 最快看到页面流程

缺点：

- 容易让后端主链路被前端假数据反向约束
- 计划容易失真

### 4.3 方案 C：数据库先收口

先补齐 ORM、Repository、事务和 schema，再向上补服务和 UI。

优点：

- 数据层稳定

缺点：

- 页面闭环出现更晚
- 与当前 `workspace` 主壳的联动价值释放慢

### 4.4 推荐结论

采用方案 A。后续执行计划必须基于“现有命名不变、主链路并入 workspace、后端分层沿用 app 现结构”来编写。

## 5. 总体架构

### 5.1 后端分层职责

- `api/`：只做 HTTP 输入输出、状态码映射、错误包装
- `services/`：组织主业务流程
- `repositories/`：负责持久化读写
- `rag/`：负责章节结构提取、切块、检索
- `agents/`：仅负责模型分析与路由，不承载持久化流程
- `schemas/`：统一请求响应结构

### 5.2 前端分层职责

- `workspace`：主界面编排与状态承载
- `document/section/analysis/chat/api`：分别提供 API 调用封装
- 必要时在 `workspace` 下新增少量 mapper 或聚合调用层，将 API 数据映射为 `WorkspacePage` 可消费结构

### 5.3 Tauri 角色

Tauri 本阶段仅作为桌面应用壳，不承担文档处理与 RAG 主业务逻辑。主链路暂按 React -> Python API 执行。

## 6. 文件落点设计

### 6.1 后端核心文件

- `backend-python/app/services/document_ingest_service.py`
- `backend-python/app/services/section_service.py`
- `backend-python/app/services/chunk_service.py`
- `backend-python/app/services/analysis_service.py`
- `backend-python/app/services/chat_service.py`
- `backend-python/app/rag/page_index_builder.py`
- `backend-python/app/rag/retriever.py`
- `backend-python/app/services/embedding_service.py`

### 6.2 后端 API 文件

- `backend-python/app/api/document_controller.py`
- `backend-python/app/api/section_controller.py`
- `backend-python/app/api/analysis_controller.py`
- `backend-python/app/api/chat_controller.py`

### 6.3 后端 schema 文件

- `backend-python/app/schemas/document_schema.py`
- `backend-python/app/schemas/section_schema.py`
- `backend-python/app/schemas/analysis_schema.py`
- `backend-python/app/schemas/chat_schema.py`

其中 `document_schema.py` 和 `section_schema.py` 目前仍接近占位，后续要补成真实协议结构。

### 6.4 前端核心文件

- `src/features/workspace/pages/WorkspacePage.tsx`
- `src/features/workspace/type.ts`
- `src/features/workspace/components/left/FileManager.tsx`
- `src/features/workspace/components/left/SectionTree.tsx`
- `src/features/workspace/components/center/DocumentViewer.tsx`
- `src/features/workspace/components/right/ChatPanel.tsx`

### 6.5 前端 API 文件

- `src/features/document/api/documentApi.ts`
- `src/features/section/api/sectionApi.ts`
- `src/features/analysis/api/analysisApi.ts`
- `src/features/chat/api/chatApi.ts`

必要时允许在 `src/features/workspace/` 下新增少量聚合层文件，但不新建第二套主流程 page。

## 7. 主链路数据流

### 7.1 上传入库

- 左栏文件管理面板发起单文件上传
- 前端通过 `documentApi` 调用后端上传接口
- `document_controller` 完成文件名、扩展名、空文件校验

### 7.2 文档实体化

- `DocumentIngestService` 调用 `ParserFactory`
- parser 输出标准化页面列表
- 服务层构造 `DocumentRecord`
- 服务层构造 `DocumentUnit[]`
- 通过现有 Repository + UnitOfWork 持久化写入

此阶段只负责“文件 -> 原文单元”，不把章节、检索、AI 逻辑混入同一职责。

### 7.3 章节构建

- `SectionService` 调用 `page_index_builder`
- 读取 `DocumentUnit` 页码、标题、metadata
- 生成 `Section[]`
- 持久化到 `sections`

`Section` 直接承担 PageIndex 树语义，不另起 `page_index_nodes`。

### 7.4 工作区加载

- 用户在 `workspace` 选择文档
- 前端先请求章节树
- 默认选中首个章节
- 左栏显示 `SectionTree`
- 中栏加载当前章节关联原文

### 7.5 原文展示

- 中栏不展示 chunks
- 中栏直接展示当前 `Section` 覆盖范围内的 `DocumentUnit` 原文内容
- 引用、查看、跳转都基于页面原文而不是基于 chunk 拼接文本

### 7.6 RAG 切块与检索

- `ChunkService` 基于 `DocumentUnit` 或章节范围生成 `Chunk[]`
- `EmbeddingService` 负责向量生成与写回
- `Retriever` 负责从 chunks 中召回相关片段
- 检索目标仅限原文 chunk，不使用 `analysis_results` 或 `chat_messages`

### 7.7 小节 AI 解析

- 右栏先按 `section_id` 查询 `AnalysisResult`
- 已有结果则直接返回
- 无结果时由 `AnalysisService` 触发分析
- 分析上下文来源于当前 section 原文和相关 chunks
- 结果写入 `analysis_results`

### 7.8 继续追问

- `ChatPanel` 发起追问
- `chatApi` 调用后端聊天接口
- `ChatService` 读取当前文档/章节上下文、相关 chunks、当前 session 历史
- 回复保存到 `ChatSession` / `ChatMessage`

## 8. 阶段设计

### 8.1 Phase 1：上传与解析

目标：打通单文件上传、解析、`DocumentRecord`/`DocumentUnit` 持久化。

结果：文档可进入 `parsed` 状态，并可被后续章节生成流程消费。

### 8.2 Phase 2：章节结构化

目标：基于 `DocumentUnit` 生成 `Section` 树并支持查询。

结果：左栏可展示章节树，中栏可按章节加载原文。

### 8.3 Phase 3：切块与检索

目标：生成 chunks、嵌入向量、原文检索能力。

结果：检索能力为 AI 解析和继续追问提供基础上下文。

### 8.4 Phase 4：章节解析

目标：围绕当前 `section_id` 生成并缓存 `AnalysisResult`。

结果：右栏可展示当前章节解析结果。

### 8.5 Phase 5：继续追问

目标：以当前文档/章节和会话历史为上下文完成追问。

结果：形成可持续的 `ChatSession` / `ChatMessage` 记录。

## 9. 状态机设计

### 9.1 文档状态

沿用现有 `DocumentStatus`：

- `uploaded`
- `parsed`
- `indexed`
- `failed`

### 9.2 状态推进

- 文件保存成功后：`uploaded`
- `DocumentUnit` 生成并持久化成功后：`parsed`
- `Section` 与 `Chunk` 均准备好且检索可用后：`indexed`
- 任一关键步骤不可恢复失败后：`failed`

不新增新的持久化状态枚举项，例如 `processing`、`embedding`、`analyzing`。这些过程态如有需要，仅作为接口层临时响应字段。

## 10. 错误处理与事务边界

### 10.1 Controller 边界

- `document_controller` 负责输入校验与 HTTP 映射
- `section_controller` 负责参数校验与结果包装
- `analysis_controller` 负责分析请求和重试请求映射
- `chat_controller` 负责会话消息接口映射

Controller 不承担业务流程编排。

### 10.2 Service 边界

- `DocumentIngestService` 负责 parser 异常、持久化异常、状态推进
- `SectionService` 负责结构构建异常
- `ChunkService` 负责切块异常与索引准备异常
- `AnalysisService` 负责模型调用异常与已有结果命中逻辑
- `ChatService` 负责消息保存、上下文组装与回复生成

### 10.3 允许降级的场景

- 路由分类失败时，`RouterAgent` 降级到综合检索
- AI 解析失败时，用户仍然可以浏览原文
- 追问失败时，保留会话和已输入消息，不影响章节浏览

### 10.4 事务切分

- `DocumentRecord + DocumentUnit`：单次事务
- `Section` 批量生成：单独事务
- `Chunk` 与 embedding：单独事务或分批事务
- `AnalysisResult`：单次事务
- `ChatMessage`：单次事务

这保证上传解析成功后，即使后续索引失败，原文仍可使用。

## 11. 前端交互设计

### 11.1 左栏

- 文件列表与上传入口合并在 `FileManager`
- 选中文档后切换到章节视图
- 文件状态需体现上传失败、解析成功、索引未完成等状态

### 11.2 中栏

- 按当前选中章节显示原文
- 支持引用指定文本发起提问
- 空态仅区分：未选章节、该章节无内容、加载失败

### 11.3 右栏

- 同一面板承接章节解析与继续追问
- 无解析时允许触发“生成解析”
- 已有解析时直接展示并继续追问
- 提问失败时不清空输入

## 12. 测试策略

### 12.1 Python 测试

- 单元测试：
  - `backend-python/tests/unit/services/`
  - `backend-python/tests/unit/parsers/`
- 集成测试：
  - `backend-python/tests/integration/api/`
  - `backend-python/tests/integration/persistence/`

### 12.2 前端测试

- `src/features/workspace/pages/WorkspacePage.test.tsx`
- `src/features/workspace/components/left/FileManager.test.tsx`
- `src/features/workspace/components/left/SectionTree.test.tsx`
- `src/features/workspace/components/center/DocumentViewer.test.tsx`
- `src/features/workspace/components/right/ChatPanel.test.tsx`

### 12.3 本阶段不要求

- 不要求新增 Tauri 业务层测试
- 不把 provider 管理、导出、历史恢复纳入主链路测试闭环

## 13. 验收标准

### 13.1 后端验收

- 上传支持格式文件后，能成功创建 `DocumentRecord` 与 `DocumentUnit`
- 能基于该文档生成 `Section` 树
- 能根据 `section_id` 返回对应原文内容
- 能生成并检索只含原文的 `Chunk`
- 能按 `section_id` 命中或生成 `AnalysisResult`
- 能创建并追加 `ChatSession` / `ChatMessage`

### 13.2 前端验收

- `workspace` 左栏可上传并看到文件状态
- 选中文档后可看到章节树
- 选中章节后中栏可看到原文
- 右栏可展示解析结果并继续追问
- 引用中栏原文到右栏提问的流程可用

### 13.3 验证命令

- `npm run test:python`
- `npm run test:python:integration`
- `npm run test:frontend`

## 14. 对执行计划的直接约束

后续对 `AI 学业助手 MVP v4.1 文档处理与 RAG 执行计划` 的修改，必须遵守以下约束：

- 不修改现有实体与表名
- 不把主页面流拆离 `workspace`
- 不把 chunk 作为中栏正文展示数据源
- 不新建第二套后端主链路命名体系
- 不把 Tauri 作为业务主逻辑承载层
- 不把 provider、导出、历史恢复混入本次主链路范围

以上约束若与旧计划冲突，以本设计文档为准。

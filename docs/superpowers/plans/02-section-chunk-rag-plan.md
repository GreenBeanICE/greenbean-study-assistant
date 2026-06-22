# Section Chunk And RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于已持久化的 `DocumentUnit` 构建章节树、章节原文接口、chunk 切分、embedding 写入和最小 RAG 检索能力。

**Architecture:** `SectionService` 从 `DocumentUnitRepository` 读取原文单元并写入 `SectionRepository`，同时通过 `SectionUnitLinkRepository` 持久化章节与原文单元的关联；`ChunkService` 从 `DocumentUnit` 生成 `Chunk` 并写入 `ChunkRepository`；`EmbeddingService` 使用 provider embedding 接口生成向量并通过 `EmbeddingRepository` 保存；`Retriever` 先用 repository 数据做最小可测相似度检索。

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, Pydantic v2, pytest, OpenAI-compatible provider。

---

## 前置条件

先完成 `01-document-persistence-api-plan.md`。本计划假设文档和原文单元已经能入库，且 `DocumentUnitRepository.list_by_document()` 可用。

开始本计划前先确认 sqlite-vec 加载策略：当前 `requirements.txt` 未声明 `sqlite-vec`，而 `init_db.py` 默认加载名为 `sqlite_vec` 的动态扩展。执行者必须先在本地和 CI 验证应采用 pip 包、系统动态库还是测试 no-op loader；确认后再修改依赖或文档，不在未验证的情况下随意固定版本。

## 范围

本计划不做 AI 分析生成、聊天会话、前端 workspace 接入和 provider 配置产品化。

## 分层约束

- `db/` 只补 `section_unit_links` 表和 ORM model，不写章节构建、chunk 切分或检索逻辑。
- `repositories/` 只提供 section、section-unit link、chunk、embedding 的保存和查询方法，不计算章节树、不切 chunk、不调用 provider。
- `rag/` 放纯算法或检索组件，例如 page index 构建、余弦相似度检索；它可以依赖 entity 或 repository 抽象，但不直接处理 HTTP。
- `services/` 负责编排 repository、rag 组件、provider 和事务边界；构建 section、chunk、embedding 时必须保持同一业务动作的写入事务清晰。
- `api/` 只暴露 section 相关 HTTP 路由，不直接操作 ORM model，不直接调用 provider embedding。
- `providers/` 只封装外部模型 API 调用，不保存 embedding，不读写业务表。
- 禁止把 AI 生成内容写入 `Chunk`；chunk 只存原文，分析结果属于后续 `AnalysisResult`。

## 文件职责

| 文件 | 操作 | 职责 |
| --- | --- | --- |
| `backend-python/app/rag/page_index_builder.py` | 修改 | 从 DocumentUnit 元数据或页码生成 Section 列表。 |
| `backend-python/app/db/init_db.py` | 修改 | 增加 `section_unit_links` 表 DDL。 |
| `backend-python/app/db/models.py` | 修改 | 增加 `SectionUnitLinkModel`。 |
| `backend-python/app/services/section_service.py` | 修改 | 章节构建、章节树查询、章节原文查询。 |
| `backend-python/app/repositories/section_repository.py` | 修改 | 增加按 document 查询。 |
| `backend-python/app/repositories/section_unit_link_repository.py` | 新增 | 保存和查询章节与 DocumentUnit 的关联。 |
| `backend-python/app/repositories/document_unit_repository.py` | 修改 | 支持按 link 结果批量读取 DocumentUnit，并保持展示顺序。 |
| `backend-python/app/schemas/section_schema.py` | 修改 | 定义章节树和章节内容响应。 |
| `backend-python/app/api/section_controller.py` | 修改 | 暴露章节构建、树查询、内容查询 API。 |
| `backend-python/app/services/chunk_service.py` | 修改 | 从 DocumentUnit 切分并保存 chunks。 |
| `backend-python/app/repositories/chunk_repository.py` | 修改 | 增加按 document unit 查询和按 document 查询辅助。 |
| `backend-python/app/providers/base.py` | 修改 | 增加 embedding 结果类型和 provider 方法。 |
| `backend-python/app/providers/openai_compat_provider.py` | 修改 | 调用 OpenAI-compatible embeddings API。 |
| `backend-python/app/services/embedding_service.py` | 修改 | 为 chunks 生成并保存 embedding。 |
| `backend-python/app/rag/retriever.py` | 修改 | 实现最小余弦相似度检索。 |
| `backend-python/app/main.py` | 修改 | 注册 section 路由。 |
| `backend-python/tests/unit/rag/test_page_index_builder.py` | 新增 | 验证章节构建规则。 |
| `backend-python/tests/unit/services/test_section_service.py` | 修改 | 验证章节 service 编排。 |
| `backend-python/tests/integration/persistence/test_section_unit_link_repository.py` | 新增 | 验证 section-unit link 表约束和 repository。 |
| `backend-python/tests/unit/services/test_chunk_service.py` | 修改 | 验证 chunk 切分。 |
| `backend-python/tests/unit/providers/test_openai_compat_provider.py` | 修改 | 验证 embedding provider。 |
| `backend-python/tests/integration/api/test_section_controller.py` | 新增 | 验证 section API。 |

## Task 1: Section Builder

- [ ] **Step 1: 写章节构建测试**

测试方向：给 `DocumentUnit` 构造三种输入：带 `metadata_json.headings`、无 headings 但有页码、空文档。断言输出 section 标题、level、order_index、start_page、end_page 稳定。

- [ ] **Step 2: 实现 `page_index_builder.py`**

实现要点：

- 函数名使用 `build_sections_from_units(document_id, units)`。
- 优先读取 `unit.metadata_json.get("headings")`；每个 heading 生成一个 `Section`。
- 没有 headings 时按页生成 fallback section，标题为 `Page <page_number>` 或 `Unit <sequence_index + 1>`。
- `parent_section_id` 暂不复杂推导；如需要树形层级，由 `SectionService._build_tree()` 根据 level 推导展示树，不强写 parent。
- 空 units 返回空列表，不抛异常。

- [ ] **Step 3: 运行 builder 测试**

Run: `npm run test:python -- tests/unit/rag/test_page_index_builder.py -v`

Expected: PASS。

## Task 2: SectionUnitLink Persistence

- [ ] **Step 1: 写 link 持久化测试**

测试方向：在 `backend-python/tests/integration/persistence/test_section_unit_link_repository.py` 中验证 `section_unit_links` 表存在；同一 section 下 `document_unit_id` 不可重复；同一 section 下 `order_index` 不可重复；`list_by_section(section_id)` 按 `order_index` 升序返回。

- [ ] **Step 2: 增加 DB 表和 ORM model**

实现要点：

- 在 `init_db.py` 的 schema 中增加 `section_unit_links` 表，字段为 `id/section_id/document_unit_id/order_index`。
- 外键分别指向 `sections.id` 和 `document_units.id`。
- 增加两个唯一约束：`(section_id, document_unit_id)` 和 `(section_id, order_index)`。
- 在 `models.py` 增加 `SectionUnitLinkModel`，字段和约束与 DDL 一致。

- [ ] **Step 3: 新增 repository**

实现要点：

- 新建 `backend-python/app/repositories/section_unit_link_repository.py`。
- 提供 `save(link: SectionUnitLink) -> SectionUnitLink`、`list_by_section(section_id: str) -> list[SectionUnitLink]`。
- 映射实体使用现有 `app.entities.SectionUnitLink`，不新增第二套 DTO。

- [ ] **Step 4: 运行 link 持久化测试**

Run: `npm run test:python -- tests/integration/persistence/test_section_unit_link_repository.py -v`

Expected: PASS。

## Task 3: Section Repository And Service

- [ ] **Step 1: 写 service 测试**

测试方向：mock unit repository 返回多页 units，验证 `build_sections(document_id)` 保存 sections、保存 section-unit links 并 commit；验证 `get_section_tree(document_id)` 返回嵌套 children；验证 `get_section_content(section_id)` 优先通过 links 返回关联 units。

- [ ] **Step 2: 补 repository 方法**

实现要点：

- `SectionRepository.list_by_document(document_id)` 按 `order_index` 升序。
- `SectionUnitLinkRepository.list_by_section(section_id)` 按 `order_index` 升序。
- `DocumentUnitRepository.list_by_ids(unit_ids)` 按传入 `unit_ids` 顺序返回，供 section content 根据 link 顺序展示原文。
- 不删除旧 section；若需要幂等，先用同 document 查询后由 service 决定是否复用。本计划采用“已有 section 则直接返回”的最小策略。

- [ ] **Step 3: 实现 `SectionService`**

实现要点：

- 构造函数接收 `section_repository`、`document_unit_repository`、`section_unit_link_repository`、可选 `uow_factory`。
- `build_sections(document_id)` 如果已有 sections，直接返回，避免重复写入。
- 保存 section 时同步生成 `SectionUnitLink`：根据 section 的 `start_page/end_page` 匹配 units，匹配不到页码时按 `sequence_index` fallback。
- `get_section_tree(document_id)` 将平铺 sections 转为树：level 小于等于栈顶时弹出，level 大于栈顶时作为子节点。
- `get_section_content(section_id)` 优先读取 `SectionUnitLinkRepository.list_by_section(section_id)`，再按 link 顺序加载 units；若 link 为空，再使用 `start_page/end_page` fallback，保证旧测试和早期数据可读。
- 找不到 section 时抛出明确的 `ValueError`，controller 映射为 404。

- [ ] **Step 4: 运行 service 测试**

Run: `npm run test:python -- tests/unit/services/test_section_service.py -v`

Expected: PASS。

## Task 4: Section API

- [ ] **Step 1: 写 API 测试**

测试方向：覆盖 `POST /api/sections/documents/{document_id}/build`、`GET /api/sections/documents/{document_id}/tree`、`GET /api/sections/{section_id}/content`。断言 404 映射和响应字段。

- [ ] **Step 2: 实现 schema 和 controller**

实现要点：

- `SectionNode` 字段包含 `id/title/level/order_index/start_page/end_page/children`。
- `SectionContentResponse` 返回 `section` 和 `units`，units 只包含展示所需字段。
- controller 只做参数接收、service 调用和异常到 HTTP 状态码映射。
- 在 `main.py` 注册 `section_controller.router`，prefix 仍为 `/api`。

- [ ] **Step 3: 运行 section API 测试**

Run: `npm run test:python -- tests/integration/api/test_section_controller.py -v`

Expected: PASS。

## Task 5: Chunk Service

- [ ] **Step 1: 写 chunk 测试**

测试方向：短文本生成 1 个 chunk；长文本按 `max_chunk_size` 和 `overlap` 生成多个 chunk；空白文本跳过；所有 chunk 保留 `document_unit_id/start_char/end_char/sequence_index`。

- [ ] **Step 2: 实现 `ChunkService`**

实现要点：

- 构造参数 `max_chunk_size=800`、`overlap=100`。
- `split_units_into_chunks(units)` 只生成实体，不写库。
- `build_chunks_for_document(document_id)` 读取 units，切分 chunks，在 UOW 中保存。
- 防止 `overlap >= max_chunk_size`，构造时直接抛 `ValueError`。
- 不把 AI 生成内容写入 chunk，chunk 只存原文。

- [ ] **Step 3: 运行 chunk 测试**

Run: `npm run test:python -- tests/unit/services/test_chunk_service.py -v`

Expected: PASS。

## Task 6: Embedding Provider And Service

- [ ] **Step 1: 写 provider embedding 测试**

测试方向：mock `AsyncOpenAI.embeddings.create`，分别验证单文本和多文本输入；多文本返回 `list[list[float]]`，单文本也规范化为 `list[list[float]]`；未显式传入 embedding model 时抛出配置错误，不默认使用 chat `model_id`。

- [ ] **Step 2: 扩展 provider 抽象**

实现要点：

- 在 `base.py` 新增 `EmbeddingResult`，字段为 `embeddings: list[list[float]]` 和 `model: str`。
- `AIProvider.create_embedding(input, model=None)` 默认抛 `NotImplementedError`。
- `OpenAICompatibleProvider.create_embedding()` 调用 `self._client.embeddings.create()`。
- 本计划不修改 `ProviderConfig` 表结构，不新增 `embedding_model` 字段。
- embedding 模型必须由调用方通过 `model` 参数显式传入；未传时抛出明确错误，避免把 chat `model_id` 当 embedding model 使用。

- [ ] **Step 3: 实现 `EmbeddingService`**

实现要点：

- 构造函数接收 `embedding_repository`、`provider` 或 `provider_getter`，避免在单元测试中依赖全局激活状态。
- `embed_chunks(chunks, model)` 批量提交文本，逐条保存 vector；`model` 为必填参数。
- 保存前检查返回 embedding 数量与 chunk 数量一致，不一致抛 `ValueError`。
- 向量维度校验交给 `EmbeddingRepository.save_for_chunk()`。

- [ ] **Step 4: 运行 provider 和 embedding 测试**

Run: `npm run test:python -- tests/unit/providers/test_openai_compat_provider.py tests/unit/services/test_embedding_service.py -v`

Expected: PASS。

## Task 7: Retriever

- [ ] **Step 1: 写 retriever 测试**

测试方向：构造 3 个 chunk embedding，query embedding 与其中一个最接近，断言 top_k 顺序、score 降序、返回 chunk_id 和 text_content。

- [ ] **Step 2: 实现最小检索**

实现要点：

- `Retriever` 依赖 repository 或 query 函数，不直接打开 DB session。
- 先用 Python 余弦相似度实现，sqlite-vec 优化不在本计划范围。
- 空索引返回空列表。
- 维度不一致的候选跳过或抛错；本计划选择跳过并记录为不可检索项。

- [ ] **Step 3: 运行 RAG 相关测试**

Run: `npm run test:python -- tests/unit/rag tests/unit/services/test_chunk_service.py tests/unit/services/test_embedding_service.py -v`

Expected: PASS。

## Task 8: Completion Check

- [ ] **Step 1: 运行本计划测试集合**

Run: `npm run test:python -- tests/unit/rag tests/unit/services/test_section_service.py tests/unit/services/test_chunk_service.py tests/unit/services/test_embedding_service.py tests/unit/providers/test_openai_compat_provider.py tests/integration/persistence/test_section_unit_link_repository.py tests/integration/api/test_section_controller.py -v`

Expected: PASS。

- [ ] **Step 2: 检查提交范围**

Run: `git status --short`

Expected: 只出现本计划涉及的后端 RAG、section、chunk、provider 和测试文件。

- [ ] **Step 3: 分阶段提交**

建议提交：先提交 section，再提交 chunk，再提交 embedding/retriever。只暂存本计划涉及的明确文件，不使用全量暂存命令。

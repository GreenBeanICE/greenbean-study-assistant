# 构建 pageindex 和 rag Design

## 目标

- 在当前已打通的“文档上传 -> 解析 -> `DocumentUnit` 持久化 -> 文档详情展示”基础上，补齐最小 `PageIndex + RAG` 主链路。
- 本次交付应覆盖：章节构建、章节与原文单元关联、章节树与章节原文 API、chunk 切分、embedding 写入、最小检索能力。
- 本次交付不接受只补占位文件的完成方式；每个阶段都必须同时落代码、测试和验证命令。

## 当前现状

- 已完成链路停留在 `DocumentUnit` 层，前端当前展示的是上传后把 `DocumentUnit` 临时映射为内容块的结果，不是真实章节树。
- `backend-python/app/rag/page_index_builder.py`、`backend-python/app/services/section_service.py`、`backend-python/app/services/chunk_service.py`、`backend-python/app/services/embedding_service.py`、`backend-python/app/rag/retriever.py`、`backend-python/app/api/section_controller.py`、`backend-python/app/schemas/section_schema.py` 目前仍是占位文件。
- `Section`、`Chunk`、`SectionUnitLink` 实体已存在，`SectionRepository`、`ChunkRepository` 也已有最基础的 `save/get_by_id` 能力，可作为这次实现的起点。
- `sqlite-vec` 在当前仓库里不是稳定前置条件，因此本次最小检索默认使用 Python 余弦相似度；`sqlite-vec` 只作为未来优化方向，不作为本次交付依赖。

## 范围与边界

### 包含范围

- `PageIndex` 构建：从 `DocumentUnit` 推导平铺 `Section` 列表。
- `SectionUnitLink` 持久化：保存章节与原文单元之间的顺序关联。
- `SectionService`：构建章节、构建树、查询章节原文。
- `Section API`：提供 `build/tree/content` 三类接口。
- `ChunkService`：从 `DocumentUnit` 切分原文 chunk。
- `EmbeddingService`：调用 provider 生成向量并写入 `EmbeddingRepository`。
- `Retriever`：基于已保存 embeddings 做最小可测检索。
- 对应单元测试、集成测试与聚合验证命令。

### 明确不做

- AI 分析生成。
- Chat/Round-trip 会话能力。
- 前端 workspace 的真实 section/rag 接入。
- 基于 `sqlite-vec` 的数据库内向量检索优化。
- provider 配置产品化扩展，例如新增独立 `embedding_model` 持久化字段。

## 分层设计

### `rag/`

- `backend-python/app/rag/page_index_builder.py` 只负责从 `DocumentUnit` 生成 `Section` 列表。
- `backend-python/app/rag/retriever.py` 只负责最小余弦相似度检索。
- 这一层不处理 HTTP，不直接管理事务，不直接操作 ORM model。

### `repositories/`

- 负责 `Section`、`SectionUnitLink`、`Chunk`、`EmbeddingVector` 的保存与查询。
- 不做章节树推导、不做 chunk 切分、不做 embedding API 调用。
- 新增的查询接口要围绕 service 的真实调用方式设计，避免只为“看起来完整”而堆方法。
- 本次需要明确补齐的最小查询能力包括：`SectionRepository.list_by_document(document_id)`、`DocumentUnitRepository.list_by_ids(unit_ids)`、`ChunkRepository.list_by_ids(ids)` 或 `list_by_document(document_id)`、`EmbeddingRepository.list_by_document(document_id)`。

### `services/`

- `SectionService` 负责编排 `DocumentUnitRepository`、`SectionRepository`、`SectionUnitLinkRepository` 和事务边界。
- `ChunkService` 负责切块规则和文档级 chunk 写入。
- `EmbeddingService` 负责 provider 调用、返回数量校验和 embedding 持久化。
- `EmbeddingService` 构造时显式接收 `embedding_dimension`，并据此构造或使用 `EmbeddingRepository`；本次不从 `app_metadata` 动态读取该值。
- service 层必须是业务动作的唯一编排层，controller 不得跨过 service 直接操作 repository 或 provider。

### `api/`

- `backend-python/app/api/section_controller.py` 只接收请求、调用 `SectionService`、映射异常到 HTTP 状态码。
- 本次只暴露 section 相关 API，不扩展 analysis/chat API。

### `providers/`

- `backend-python/app/providers/base.py` 增加 embedding 抽象与返回结构。
- `backend-python/app/providers/openai_compat_provider.py` 负责调 OpenAI-compatible embeddings API。
- provider 只负责外部调用，不持久化 embedding，不读写业务表。
- `create_embedding` 的输入类型明确为 `str | list[str]`，但返回值统一规范化为 `EmbeddingResult(embeddings: list[list[float]], model: str)`。

## 执行清单

### 阶段 1: PageIndex / Section Builder

**目标**

- 从 `DocumentUnit` 自动生成稳定的 `Section` 列表，作为后续 section tree 和 section content 的基础。

**涉及文件**

- 修改 `backend-python/app/rag/page_index_builder.py`
- 新增 `backend-python/tests/unit/rag/test_page_index_builder.py`

**设计约束**

- 入口函数使用 `build_sections_from_units(document_id, units)`。
- 优先读取 `unit.metadata_json.get("headings")`。
- 没有 headings 时按页号回退，标题为 `Page <page_number>`；无页号时标题为 `Unit <sequence_index + 1>`。
- 该阶段只生成平铺 sections，不复杂推导 `parent_section_id`。
- 空 `units` 返回空列表，不抛异常。

**完成定义**

- 能覆盖 headings、页号 fallback、空文档三种输入。
- 测试命令：`npm run test:python -- tests/unit/rag/test_page_index_builder.py -v`

### 阶段 2: SectionUnitLink 持久化

**目标**

- 建立章节与原文单元的显式多对多顺序关联，避免后续章节内容只能靠页码猜测。

**涉及文件**

- 修改 `backend-python/app/db/init_db.py`，在 `_create_schema()` 中新增 `section_unit_links` 表 DDL
- 修改 `backend-python/app/db/models.py`，新增 `SectionUnitLinkModel`
- 新增 `backend-python/app/repositories/section_unit_link_repository.py`
- 新增 `backend-python/tests/integration/persistence/test_section_unit_link_repository.py`

**设计约束**

- `section_unit_links` 表字段固定为 `id/section_id/document_unit_id/order_index`。
- 外键分别指向 `sections.id` 与 `document_units.id`。
- 必须有两个唯一约束：`(section_id, document_unit_id)` 与 `(section_id, order_index)`。
- 同步为 `sections` 表增加 `(document_id, order_index)` 唯一约束，避免并发重复构建时生成重复 section。
- repository 至少提供 `save()` 和 `list_by_section()`。

**完成定义**

- 表存在且唯一约束生效。
- `list_by_section(section_id)` 按 `order_index` 升序返回。
- 测试命令：`npm run test:python -- tests/integration/persistence/test_section_unit_link_repository.py -v`

### 阶段 3: SectionService 与 Section API

**目标**

- 让后端能真正构建章节树并返回章节原文，而不是只持久化平铺 section。

**涉及文件**

- 修改 `backend-python/app/services/section_service.py`
- 修改 `backend-python/app/db/init_db.py`
- 修改 `backend-python/app/db/models.py`
- 修改 `backend-python/app/repositories/section_repository.py`
- 修改 `backend-python/app/repositories/document_unit_repository.py`
- 修改 `backend-python/app/schemas/section_schema.py`
- 修改 `backend-python/app/api/section_controller.py`
- 修改 `backend-python/app/main.py`
- 修改 `backend-python/tests/unit/services/test_section_service.py`
- 新增 `backend-python/tests/integration/api/test_section_controller.py`

**设计约束**

- `build_sections(document_id)` 若已有 sections，直接返回已有结果，采用最小幂等策略。
- 保存 section 时同步保存 `SectionUnitLink`。
- `SectionRepository` 必须补 `list_by_document(document_id)`，供幂等判断和树查询复用。
- `DocumentUnitRepository` 必须补 `list_by_ids(unit_ids)`，并按传入顺序返回结果。
- `get_section_tree(document_id)` 在 service 中把平铺 sections 转为嵌套树。
- `get_section_content(section_id)` 优先按 link 顺序取 units；若 link 为空，再按页码范围 fallback。
- 找不到 section 时抛明确 `ValueError`，controller 映射为 `404`。
- `Section API` 至少包含：
  - `POST /api/sections/documents/{document_id}/build`
  - `GET /api/sections/documents/{document_id}/tree`
  - `GET /api/sections/{section_id}/content`

**完成定义**

- 能构建章节树并返回章节内容。
- API 覆盖成功路径和 404 映射。
- `main.py` 已注册 `section_controller.router`，section 路由可以真实访问。
- 测试命令：
  - `npm run test:python -- tests/unit/services/test_section_service.py -v`
  - `npm run test:python -- tests/integration/api/test_section_controller.py -v`

### 阶段 4: ChunkService

**目标**

- 从 `DocumentUnit` 生成可追溯到原文单元的 chunks，为 embedding 和检索做准备。

**涉及文件**

- 修改 `backend-python/app/services/chunk_service.py`
- 修改 `backend-python/app/repositories/chunk_repository.py`
- 修改 `backend-python/tests/unit/services/test_chunk_service.py`

**设计约束**

- 构造参数默认 `max_chunk_size=800`、`overlap_chars=100`；这里的 overlap 单位明确为字符数。
- `split_units_into_chunks(units)` 只生成实体，不写库。
- `build_chunks_for_document(document_id)` 的调用链固定为：`DocumentUnitRepository.list_by_document(document_id)` -> `split_units_into_chunks(units)` -> 事务内保存 chunks。
- 若 `overlap_chars >= max_chunk_size`，构造时直接抛 `ValueError`。
- 空白文本跳过；chunk 只保存原文，不写 AI 生成内容。

**完成定义**

- 短文本生成 1 个 chunk，长文本按窗口切成多个 chunk，并保留 `document_unit_id/start_char/end_char/sequence_index`。
- 测试命令：`npm run test:python -- tests/unit/services/test_chunk_service.py -v`

### 阶段 5: Embedding Provider 与 EmbeddingService

**目标**

- 为已生成的 chunks 批量创建 embeddings 并写入 `EmbeddingVector`。

**涉及文件**

- 修改 `backend-python/app/providers/base.py`
- 修改 `backend-python/app/providers/openai_compat_provider.py`
- 修改 `backend-python/app/services/embedding_service.py`
- 修改 `backend-python/tests/unit/providers/test_openai_compat_provider.py`
- 新增 `backend-python/tests/unit/services/test_embedding_service.py`

**设计约束**

- 在 `base.py` 新增 `EmbeddingResult`，至少包含 `embeddings` 与 `model`。
- `AIProvider.create_embedding(input, model=None)` 作为显式抽象加入 provider 基类。
- `OpenAICompatibleProvider.create_embedding()` 直接调用 `self._client.embeddings.create()`。
- embedding 模型必须由调用方通过 `model` 参数显式传入；未传时抛错，不回退到 chat `model_id`。
- `EmbeddingService.embed_chunks(chunks, model)` 必须校验“返回 embedding 数量 == chunk 数量”。
- 如果数量不匹配或任一向量保存失败，整个批次回滚，不允许落部分 embeddings。
- provider 测试统一用 `unittest.mock.patch` mock `AsyncOpenAI.embeddings.create`。

**完成定义**

- provider 支持单文本和多文本 embedding。
- service 能逐条保存向量并在数量不匹配时显式失败。
- 测试命令：`npm run test:python -- tests/unit/providers/test_openai_compat_provider.py tests/unit/services/test_embedding_service.py -v`

### 阶段 6: Retriever

**目标**

- 基于已保存 embeddings 产出最小可测的 chunk 检索结果。

**涉及文件**

- 修改 `backend-python/app/rag/retriever.py`
- 修改 `backend-python/app/repositories/chunk_repository.py`
- 修改 `backend-python/app/repositories/embedding_repository.py`
- 新增 `backend-python/tests/unit/rag/test_retriever.py`

**设计约束**

- `Retriever` 构造时显式接收 `EmbeddingRepository` 与 `ChunkRepository`，不直接打开 DB session。
- 先用 Python 余弦相似度实现，不依赖 `sqlite-vec`。
- 空索引返回空列表。
- 维度不一致候选跳过，不因单条坏数据让整个检索失败。
- 检索流程固定为：先从 `EmbeddingRepository.list_by_document(document_id)` 取 embeddings，再计算余弦相似度，再用 `ChunkRepository.list_by_ids(ids)` 取 chunk 文本，最后返回 `chunk_id/text_content/score`。
- 返回结果至少包含 `chunk_id`、`text_content`、`score`。

**完成定义**

- 给定 query embedding 时，能稳定按 `score` 降序返回 `top_k`。
- 测试命令：`npm run test:python -- tests/unit/rag/test_retriever.py -v`

### 阶段 7: 聚合验证

**目标**

- 证明这次交付形成了真正可工作的最小 `PageIndex + RAG` 后端主链路。

**验证命令**

- `npm run test:python -- tests/unit/rag tests/unit/services/test_section_service.py tests/unit/services/test_chunk_service.py tests/unit/services/test_embedding_service.py tests/unit/providers/test_openai_compat_provider.py tests/integration/persistence/test_section_unit_link_repository.py tests/integration/api/test_section_controller.py -v`
- `git status --short`

**完成定义**

- 上述测试集合全部通过。
- 工作区只出现本次 `pageindex/rag/section/chunk/provider` 相关改动。

## 风险与处理

- `sqlite-vec` 本机与 CI 环境不稳定：本次先不把它作为检索前置，避免 RAG 实现被环境问题阻塞。
- 早期文档数据可能没有 headings：统一提供页号与顺序 fallback，确保 section 主链路先可用。
- embedding provider 容易误用 chat 模型：通过“必须显式传 `model`”把错误暴露在调用层，而不是静默降级。
- 章节内容如果只靠页码推断容易错位：通过 `SectionUnitLink` 做主路径，页码范围只做兼容 fallback。

## 测试策略

- 单元测试聚焦纯规则：`page_index_builder`、`chunk_service`、`embedding_service`、`retriever`、provider embeddings。
- 集成测试使用真实 SQLite schema，不 mock ORM；沿用仓库现有的 `initialize_database + create_database_engine + create_session_factory` fixture 组合，优先使用 `tmp_path` 下的临时数据库文件而不是额外发明一套测试基建。
- `test_section_controller.py` 走真实 FastAPI + 真实 session factory，覆盖成功路径和异常映射。

## 最终完成标准

- 后端可以从已解析文档构建 `Section` 和 `SectionUnitLink`。
- 可以通过 API 获取章节树和章节原文内容。
- 可以为文档生成 chunks，并为 chunks 生成和保存 embeddings。
- 可以基于 query embedding 做最小 chunk 检索。
- 全流程至少由单测与集成测试覆盖，不存在“代码在、测试缺失”或“测试在、实现仍是占位”的状态。

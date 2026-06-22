# Document Persistence And API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成单文件上传后的 `DocumentRecord` 与 `DocumentUnit` 持久化，并提供文档上传、列表和详情 API。

**Architecture:** 沿用当前 `api -> services -> repositories -> db` 分层。`DocumentIngestService` 只负责解析、实体构建和上传持久化；`DocumentQueryService` 负责文档列表和详情查询（只读）。事务边界放在 service 内，repository 由当前 UOW session 创建，避免跨 session 写入。controller 只依赖 service，不直接 import repository。

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, Pydantic v2, pytest。

---

## 范围

本计划只覆盖文档摄取入库和文档查询 API，不做章节、chunk、embedding、分析、聊天和前端 workspace 集成。

## 分层约束

- `db/` 只提供数据库初始化、engine、session factory、UOW 和 ORM model，不承载文档业务逻辑。
- `repositories/` 只负责 ORM model 与 Pydantic entity 的持久化映射，不调用 parser、不做上传校验、不管理 HTTP 状态码。
- `services/` 负责编排 parser、entity 构建、repository 调用和事务边界；同一次写入必须使用同一个 `uow.session` 创建 repository。
- `api/` 只处理 HTTP 输入输出、文件校验、异常到状态码映射和 schema 转换，不直接创建 SQLAlchemy session，不直接操作 ORM model。
- `schemas/` 只定义 API 请求/响应协议，不把 `DocumentRecord`、`DocumentUnit` entity 原样暴露给前端。
- `api/dependencies.py` 集中装配 session factory、UOW factory 和 service，避免 controller 内部分散 new 依赖。
- 禁止跨层反向依赖：repository 不能 import service/parser/controller，db 不能 import repository/service，schema 不能 import repository。

## 文件职责

| 文件 | 操作 | 职责 |
| --- | --- | --- |
| `backend-python/app/db/connection.py` | 修改 | 作为 app-level 聚合入口，组合现有 `init_db.py`、`orm.py`、`unit_of_work.py`，不搬迁底层实现。 |
| `backend-python/app/api/dependencies.py` | 新增 | 集中提供 session factory、UOW、service 依赖。 |
| `backend-python/app/services/document_ingest_service.py` | 修改 | 在解析成功后用同一个 UOW session 写入 document 和 units。 |
| `backend-python/app/services/document_query_service.py` | 新增 | 负责文档列表和详情查询，通过 UOW session 创建 repository 只读查询，不调用 commit。 |
| `backend-python/app/services/document_query_service.py` | 新增 | 提供文档列表和详情查询，避免 controller 直接依赖 repository，也避免摄取 service 职责膨胀。 |
| `backend-python/app/repositories/document_repository.py` | 修改 | 增加按 workspace 列表查询。 |
| `backend-python/app/repositories/document_unit_repository.py` | 修改 | 增加按 document 列表查询。 |
| `backend-python/app/schemas/document_schema.py` | 修改 | 定义上传响应、列表项、详情响应。 |
| `backend-python/app/api/document_controller.py` | 修改 | 接入依赖注入，补列表与详情路由。 |
| `backend-python/tests/unit/db/test_connection.py` | 新增 | 验证 DB bootstrap。 |
| `backend-python/tests/unit/services/test_document_ingest_service.py` | 修改 | 验证 service 持久化编排。 |
| `backend-python/tests/unit/services/test_document_query_service.py` | 新增 | 验证 query service 列表和详情查询逻辑。 |
| `backend-python/tests/integration/api/test_document_controller.py` | 修改 | 验证上传、列表、详情 API。 |
| `backend-python/tests/integration/persistence/test_sqlite_repositories.py` | 修改 | 验证新增 repository 查询方法。 |

## Task 1: DB Bootstrap

- [x] **Step 1: 写 DB bootstrap 测试**

测试方向：在 `backend-python/tests/unit/db/test_connection.py` 中验证 `create_app_session_factory()` 返回可用 session factory，`:memory:` 模式不会创建真实 data 文件；验证 `create_app_uow()` 返回 `SqlAlchemyUnitOfWork`；验证实现仍调用现有 `initialize_database()`、`create_database_engine()`、`create_session_factory()`，不复制这些函数的逻辑。

实施约束：不要顺手重构 `backend-python/tests/integration/persistence/test_sqlite_repositories.py` 里现有的 `session_factory` fixture。Task 1 只新增 DB bootstrap 的单元测试，避免扩大持久化集成测试变更面。

- [x] **Step 2: 实现 `connection.py`**

实现要点：

- `create_app_session_factory(database_path, embedding_dimension, sqlite_vec_loader)` 调用现有 `initialize_database()` 初始化真实文件数据库，再调用现有 `create_database_engine()` 和 `create_session_factory()`。
- `:memory:` 用于单元测试时直接创建 engine，不调用 `initialize_database()`，并允许传入 no-op `sqlite_vec_loader`。
- `create_app_uow(session_factory)` 只包装 `SqlAlchemyUnitOfWork(session_factory)`。
- 不把 `orm.py`、`init_db.py`、`unit_of_work.py` 的实现搬到 `connection.py`；`connection.py` 只做应用启动所需的轻量组合。
- 不在此文件创建 repository，repository 必须在 UOW session 打开后创建。
- 不要重构 `tests/integration/persistence/test_sqlite_repositories.py` 现有的 `session_factory` fixture；该 fixture 继续直接组合 `initialize_database` + `create_database_engine` + `create_session_factory`，Task 1 只新增聚合入口，不强制收敛已有测试。

- [x] **Step 3: 运行 DB 测试**

Run: `npm run test:python -- tests/unit/db/test_connection.py -v`

Expected: PASS。

## Task 2: Repository Query Methods

- [x] **Step 1: 写 repository 查询测试**

测试方向：在 `test_sqlite_repositories.py` 中插入两个 workspace 的文档和 units，断言 `DocumentRepository.list_by_workspace(workspace_id)` 只返回目标 workspace，按创建时间或标题稳定排序；断言 `DocumentUnitRepository.list_by_document(document_id)` 按 `sequence_index` 升序返回。

- [x] **Step 2: 实现查询方法**

实现要点：

- `DocumentRepository.list_by_workspace(workspace_id: str) -> list[DocumentRecord]` 使用 SQLAlchemy `select(DocumentRecordModel)`。
- `DocumentUnitRepository.list_by_document(document_id: str) -> list[DocumentUnit]` 使用 `order_by(DocumentUnitModel.sequence_index)`。
- 复用现有 model -> entity 映射逻辑，必要时提取私有 `_to_entity()`，但不要重构其他 repository。

- [x] **Step 3: 运行持久化测试**

Run: `npm run test:python -- tests/integration/persistence/test_sqlite_repositories.py -v`

Expected: PASS。

## Task 3: DocumentIngestService Persistence

- [x] **Step 1: 写 service 持久化测试**

测试方向：mock parser 输出两页内容，注入真实或 fake UOW factory，验证 `ingest_document()` 成功后 document 保存一次、unit 保存两次、commit 一次；失败时不提交，异常向上抛出。

- [x] **Step 2: 调整 service 构造方式**

实现要点：

- `DocumentIngestService` 接收 `uow_factory` 或 `session_factory`，不要接收已绑定旧 session 的 repository 实例。
- 无 UOW 时只保留当前内存返回能力，方便单元测试继续验证实体构建；生产路径必须通过 `uow_factory` 持久化，不保留旧的 repository 直注入生产路径。
- 有 UOW 时在 `with self.uow_factory() as uow:` 内创建 `DocumentRepository(uow.session)` 和 `DocumentUnitRepository(uow.session)`。
- 保存顺序必须是 document 先保存，units 后保存，最后 commit。
- service 内使用 `with self.uow_factory() as uow:` 管理事务，依赖 `SqlAlchemyUnitOfWork.__exit__` 在异常时自动 rollback；不要在 service 内额外包 try/except 吞异常。
- 返回结构继续包含 `document_record`、`document_units`、`filename`、`total_pages`、`status`、`page_index_preview`。

- [x] **Step 3: 运行 service 测试**

Run: `npm run test:python -- tests/unit/services/test_document_ingest_service.py -v`

Expected: PASS。

## Task 4: Document Query Service, Schemas And API

- [x] **Step 1: 写 DocumentQueryService 测试**

测试方向：在 `backend-python/tests/unit/services/test_document_query_service.py` 中注入 fake 或真实 UOW，验证 `list_by_workspace(workspace_id)` 只返回目标 workspace 的文档，按稳定排序；`get_document_detail(document_id)` 在文档存在时返回包含 document 和 units 的结构，不存在时返回 None。

- [x] **Step 2: 实现 DocumentQueryService**

实现要点：

- 新建 `backend-python/app/services/document_query_service.py`。
- `DocumentQueryService(uow_factory)` 在查询方法内通过 `with uow_factory() as uow:` 打开 session，创建 `DocumentRepository(uow.session)` 和 `DocumentUnitRepository(uow.session)`。
- `list_by_workspace(workspace_id)` 调用 `DocumentRepository.list_by_workspace()`，返回 `list[DocumentRecord]`。
- `get_document_detail(document_id)` 调用 `DocumentRepository.get_by_id()`；不存在返回 None；存在时再调用 `DocumentUnitRepository.list_by_document()`，返回包含 document 和 units 的结构。
- 只读不写，不调用 commit。

- [x] **Step 3: 写 API 测试**

测试方向：覆盖 `POST /api/documents/upload`、`GET /api/documents?workspace_id=workspace_1`、`GET /api/documents/{document_id}`。断言上传响应使用 `DocumentUploadResponse` schema，不直接暴露 Pydantic entity；列表响应字段稳定，不返回 `file_path`；详情包含 document 和 units；详情 404 当文档不存在。dependency override 必须针对 `app.api.dependencies.get_ingest_service` 和 `app.api.dependencies.get_document_query_service`，且 override key 必须与 controller `Depends(...)` 引用的是同一个函数对象。

- [x] **Step 4: 实现 schema**

实现要点：

- `DocumentUploadResponse` 返回 `id/title/original_filename/file_type/status/page_count/created_at`。
- `DocumentListItem` 返回列表所需字段，不返回 `file_path`。
- `DocumentDetailResponse` 返回 document 基本信息和 units 简要字段。
- enum 字段对外输出字符串值。
- 文档相关 schema 统一放在 `document_schema.py`；`upload_schema.py` 保持占位但本计划不继续扩展，避免两个文件同时定义上传响应。

- [x] **Step 5: 新增 `api/dependencies.py`**

实现要点：

- 集中装配 session factory、UOW factory、`DocumentIngestService` 和 `DocumentQueryService`。
- `get_ingest_service()` 返回绑定了 UOW factory 的 `DocumentIngestService`。
- `get_document_query_service()` 返回绑定了 UOW factory 的 `DocumentQueryService`。
- Phase 1 的 session factory 可以是延迟初始化的 app-level factory；具体装配方式在实现时确定，但不允许在 controller 内部 new 依赖。

- [x] **Step 6: 调整 controller**

实现要点：

- 删除 controller 内的 `get_ingest_service`，改为从 `app.api.dependencies` import。
- `upload_document()` 继续保留文件名、格式、空内容校验。
- 上传时允许可选 `workspace_id` form 字段；未传时使用当前默认 `workspace_1`，后续多 workspace 不在本计划范围。
- `list_documents(workspace_id, query_service)` 调用 `query_service.list_by_workspace()`，返回 `list[DocumentListItem]`。
- `get_document_detail(document_id, query_service)` 调用 `query_service.get_document_detail()`，不存在时返回 404。
- controller 只通过 `Depends` 注入 `DocumentIngestService` 和 `DocumentQueryService`，不直接 import repository，不直接创建 SQLAlchemy session。

- [x] **Step 7: 运行 query service 与 API 测试**

Run: `npm run test:python -- tests/unit/services/test_document_query_service.py tests/integration/api/test_document_controller.py -v`

Expected: PASS。

## Task 5: Completion Check

- [x] **Step 1: 运行相关测试集合**

Run: `npm run test:python -- tests/unit/db tests/unit/services/test_document_ingest_service.py tests/unit/services/test_document_query_service.py tests/integration/api/test_document_controller.py tests/integration/persistence/test_sqlite_repositories.py -v`

Expected: PASS。

- [x] **Step 2: 检查提交范围**

Run: `git status --short`

Expected: 只出现本计划涉及的文件。

- [x] **Step 3: 分阶段提交**

建议提交：`git add backend-python/app/db/connection.py backend-python/app/api/dependencies.py backend-python/app/services/document_ingest_service.py backend-python/app/services/document_query_service.py backend-python/app/repositories/document_repository.py backend-python/app/repositories/document_unit_repository.py backend-python/app/schemas/document_schema.py backend-python/app/api/document_controller.py backend-python/tests/unit/db/test_connection.py backend-python/tests/unit/services/test_document_ingest_service.py backend-python/tests/unit/services/test_document_query_service.py backend-python/tests/integration/api/test_document_controller.py backend-python/tests/integration/persistence/test_sqlite_repositories.py`。

Commit: `git commit -m "feat: persist ingested documents and expose document APIs"`。

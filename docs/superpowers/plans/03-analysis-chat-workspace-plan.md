# Analysis Chat And Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于已完成的文档、章节和 RAG 能力，实现章节 AI 解析、继续追问 API，并把前端 `workspace` 主页面接入真实 API。

**Architecture:** 后端由 `AnalysisService` 和 `ChatService` 编排 agents、repositories 与 RAG context；controller 只暴露 HTTP 协议。前端保留当前 workspace 三栏布局，`document/section/analysis/chat/api` 作为数据访问层，`WorkspacePage` 负责页面状态编排。

**Tech Stack:** FastAPI, Pydantic v2, pytest, React 19, TypeScript, Vitest, Testing Library。

---

## 前置条件

先完成 `01-document-persistence-api-plan.md` 和 `02-section-chunk-rag-plan.md`。本计划假设文档、章节、chunk、embedding 和最小检索能力已经可用。

## 范围

本计划只覆盖章节解析、继续追问和 workspace 主链路接入。不做导出、provider 配置 UI、历史恢复扩展、多 workspace 切换和 Tauri 业务逻辑。

## 分层约束

- 后端 `api/` 只做 HTTP 协议、参数校验和异常映射，不直接读取 ORM model，不拼 prompt，不打开 DB session。
- 后端 `services/` 负责 analysis/chat 主流程编排，包括取章节上下文、调用 agent、保存结果和消息；事务边界必须在 service 层清晰管理。
- 后端 `agents/` 只负责模型提示词和 provider 调用编排，不直接写 repository，不决定 HTTP 状态码。
- 后端 `repositories/` 只做 `AnalysisResult`、`ChatSession`、`ChatMessage` 的持久化查询，不构造 prompt，不调用 agent。
- 前端 `features/*/api` 只做 API DTO 和请求封装，不持有 workspace UI 状态。
- 前端 `workspace` 负责三栏页面状态编排和 DTO 到 UI model 的映射，不把业务请求散落到子组件中。
- Tauri 不承载本计划业务逻辑；主链路仍按 React -> Python API 执行。
- 首次章节解析不能读取 chat history；继续追问默认上下文只含原文 chunks、当前章节上下文和当前会话历史。

## 文件职责

| 文件 | 操作 | 职责 |
| --- | --- | --- |
| `backend-python/app/services/analysis_service.py` | 修改 | 获取章节上下文、复用已有分析、调用 agent、保存结果。 |
| `backend-python/app/api/analysis_controller.py` | 修改 | 暴露生成和查询分析 API。 |
| `backend-python/app/repositories/analysis_result_repository.py` | 修改 | 增加按 section 查询。 |
| `backend-python/app/services/chat_service.py` | 修改 | 创建会话、保存消息、调用 chat agent。 |
| `backend-python/app/agents/chat_agent.py` | 修改 | 从 mock context 切换为注入的上下文。 |
| `backend-python/app/api/chat_controller.py` | 修改 | 暴露发送消息 API。 |
| `backend-python/app/api/provider_controller.py` | 修改 | 如需 HTTP 验证 provider 激活，补最小 APIRouter 包装，不做 provider 配置产品化。 |
| `backend-python/app/repositories/chat_session_repository.py` | 修改 | 增加会话查询辅助。 |
| `backend-python/app/repositories/chat_message_repository.py` | 修改 | 增加按 session 查询。 |
| `backend-python/app/main.py` | 修改 | 注册 analysis 和 chat 路由。 |
| `src/lib/apiClient.ts` | 修改 | 封装 API base、JSON 请求、错误处理。 |
| `src/features/document/api/documentApi.ts` | 修改 | 上传、列表、详情 API。 |
| `src/features/section/api/sectionApi.ts` | 修改 | 章节树和章节内容 API。 |
| `src/features/analysis/api/analysisApi.ts` | 修改 | 章节解析 API。 |
| `src/features/chat/api/chatApi.ts` | 修改 | 发送消息 API。 |
| `src/types/chat.ts` | 修改 | 将前端消息角色从 `assistant` 统一为后端的 `agent`。 |
| `src/features/workspace/components/right/ChatPanel.tsx` | 修改 | 使用 `agent` 判断 AI 消息。 |
| `src/features/workspace/type.ts` | 修改 | 补充 workspace 状态类型。 |
| `src/features/workspace/pages/WorkspacePage.tsx` | 修改 | 接入真实 API 并保留三栏主壳。 |
| `src/features/workspace/pages/WorkspacePage.test.tsx` | 修改 | 验证主要交互。 |

## Task 1: Analysis Service And API

- [ ] **Step 1: 写 analysis repository/service 测试**

测试方向：已有 section 分析时直接返回，不重复调用 agent；没有分析时从 section content 构造 context，调用 agent，保存 `AnalysisResult`；agent 失败时不写库并向 controller 映射为 500。

- [ ] **Step 2: 补 repository 方法**

实现要点：

- `AnalysisResultRepository.get_by_section_id(section_id)` 返回最新一条 section 分析。
- 如果未来支持多 analysis type，再扩展为按 `section_id + analysis_type + language` 查询；本计划只做章节解析默认中文。

- [ ] **Step 3: 实现 `AnalysisService`**

实现要点：

- 将当前函数式/演示性质实现收敛为 `AnalysisService` 类；迁移后 controller 和测试都只依赖类方法，不再直接调用旧演示函数。
- 复用现有 `build_markdown_from_json()`，不要重复实现 Markdown 生成逻辑。
- 将现有 `process_and_save_analysis()` 的实体组装逻辑迁移到 `get_or_create_section_analysis()`；迁移后旧函数可作为兼容薄包装或移除，由执行者根据现有测试决定。
- 构造函数接收 `analysis_repository`、`section_service`、`analysis_agent`、可选 `uow_factory`。
- `get_or_create_section_analysis(document_id, section_id)` 先查已有结果。
- context 来自 `section_service.get_section_content(section_id)`，把 units 的 `text_content` 按顺序拼接。
- agent 返回结构化内容时，同时保存 `content_json` 和可展示 `content_markdown`。
- 不读取 chat history，不把聊天内容混入首次章节解析。

- [ ] **Step 4: 实现 analysis controller**

实现要点：

- `POST /api/analysis/sections/{section_id}/generate`，请求体包含 `document_id`。
- `GET /api/analysis/sections/{section_id}` 查询已有解析。
- 找不到 section 或 document 时返回 404，provider 未配置返回 409，其他异常返回 500。
- 在 `main.py` 注册路由。

- [ ] **Step 5: 运行 analysis 测试**

Run: `npm run test:python -- tests/unit/services/test_analysis_service.py tests/integration/api/test_analysis_controller.py -v`

Expected: PASS。

## Task 2: Chat Service And API

- [ ] **Step 1: 写 chat service 测试**

测试方向：无 session_id 时创建 session；有 session_id 时复用会话；每次提问保存 user 和 agent 两条消息；传入 section_id 时优先使用当前章节上下文；默认上下文只含原文 chunks 和当前会话历史。

- [ ] **Step 2: 补 chat repositories**

实现要点：

- `ChatSessionRepository.get_by_id(session_id)` 已有则复用，没有则新增。
- `ChatMessageRepository.list_by_session(session_id)` 按 `created_at` 升序。
- 保存 user 和 agent 消息必须在同一个事务内提交。

- [ ] **Step 3: 调整 `ChatAgent`**

实现要点：

- 移除当前硬编码 mock context。
- `generate_response()` 接收已经构造好的 `context_text` 或 `source_context`。
- route 分类可保留，但不阻塞基础回答；分类失败时走普通问答。

- [ ] **Step 4: 实现 `ChatService`**

实现要点：

- 构造函数接收 session/message repositories、chat_agent、retriever 或 context_builder、可选 uow_factory。
- `send_message(workspace_id, document_id, section_id, session_id, query)` 返回 `ChatResponse`。
- 没有 session_id 时创建标题为 query 前 50 字的新会话。
- context 构造顺序：当前 section 原文优先，其次 document chunk 检索，其次空 context。
- 保存 agent 消息时写入 `source_context_json`，便于前端展示引用。

- [ ] **Step 5: 实现 chat controller**

实现要点：

- `POST /api/chat/messages` 请求体包含 `workspace_id/document_id/section_id/session_id/query`。
- 空 query 返回 400。
- session 不存在返回 404。
- provider 未配置返回 409。
- 在 `main.py` 注册路由。

- [ ] **Step 6: 确认 provider 激活入口**

实现要点：

- 当前 `provider_controller.py` 是 class 风格，不是 FastAPI `APIRouter`。
- 如果 analysis/chat API 集成测试需要通过 HTTP 激活 provider，则在 `provider_controller.py` 中补最小 `router = APIRouter(prefix="/providers")` 包装现有 `ProviderController` 方法，并在 `main.py` 注册。
- 如果测试通过 service/repository/registry 直接注入 provider，则记录为测试策略，不在本计划扩展完整 provider 管理 API。
- 不新增 provider 配置 UI，不引入 provider 配置产品化流程。

- [ ] **Step 7: 运行 chat 测试**

Run: `npm run test:python -- tests/unit/services/test_chat_service.py tests/integration/api/test_chat_controller.py -v`

Expected: PASS。

## Task 3: Frontend API Layer

- [ ] **Step 1: 统一前端 MessageRole**

测试方向：更新 `src/types/chat.ts`、`ChatPanel.tsx`、`ChatPanel.test.tsx`、`WorkspacePage.tsx`、`WorkspacePage.test.tsx` 中的消息角色断言，确保前端使用 `user | agent`，不再生成或判断 `assistant`。

实现要点：

- `src/types/chat.ts` 中 `MessageRole` 改为 `"user" | "agent"`。
- `ChatPanel.tsx` 中 AI 头像和标签判断从 `msg.role === "assistant"` 改为 `msg.role === "agent"`。
- `WorkspacePage.tsx` 中本地临时 AI 回复对象使用 `role: "agent"`。
- 所有测试数据同步使用 `agent`。

- [ ] **Step 2: 写 API 层测试或 mock 约束**

测试方向：mock `fetch`，验证各 API 使用正确 URL、method、body；错误响应时抛出带后端 `detail` 的 Error。

- [ ] **Step 3: 实现 `src/lib/apiClient.ts`**

实现要点：

- 定义单一 `API_BASE`，默认 `http://localhost:8000/api`。
- 提供 `getJson()`, `postJson()`, `postForm()`。
- 非 2xx 时读取 `{detail}` 或 `{message}`，抛 `Error`。
- 不在每个 feature API 文件重复硬编码 base URL。
- 使用浏览器原生 `fetch`，不引入 axios 或其他 HTTP client。

- [ ] **Step 4: 实现 feature API 文件**

实现要点：

- `documentApi.ts`：`uploadDocument(file, workspaceId)`, `listDocuments(workspaceId)`, `getDocumentDetail(documentId)`。
- `sectionApi.ts`：`buildSections(documentId)`, `getSectionTree(documentId)`, `getSectionContent(sectionId)`。
- `analysisApi.ts`：`generateSectionAnalysis(documentId, sectionId)`, `getSectionAnalysis(sectionId)`。
- `chatApi.ts`：`sendMessage(request)`。
- 类型优先复用 `src/types/*`；差异较大时在 feature API 文件定义响应 DTO，再在 workspace 映射。

- [ ] **Step 5: 运行前端 API 测试**

Run: `npm run test:frontend -- src/features/document/api src/features/section/api src/features/analysis/api src/features/chat/api src/lib/apiClient.test.ts`

Expected: PASS。

## Task 4: Workspace Integration

- [ ] **Step 1: 写 WorkspacePage 交互测试**

测试方向：迁移现有 `WorkspacePage.test.tsx` 中基于 mock 数据的大量断言，改为基于 API mock 的交互测试。页面加载时请求文档列表；选择文件后请求章节树；选择章节后请求章节内容；点击生成解析后右栏显示解析结果；发送追问后追加 user 和 agent 消息。

实施提示：当前 `WorkspacePage.test.tsx` 已有大量 mock UI 行为测试，不要一次性删除重写。先保留布局、折叠、拖拽等纯 UI 测试，再分批替换依赖硬编码文档/章节/聊天假数据的测试。

- [ ] **Step 2: 调整 workspace state 类型**

实现要点：

- 在 `src/features/workspace/type.ts` 增加 `documents`、`selectedDocumentId`、`selectedSectionId`、`analysisMarkdown`、`apiError`、`loadingTarget` 等必要字段。
- 保留现有三栏布局和折叠/拖拽状态，不重写 UI 结构。

- [ ] **Step 3: 接入真实 API**

实现要点：

- 初始加载调用 `listDocuments("workspace_1")`。
- 上传成功后刷新文档列表并自动选中新文档。
- 选择文档后调用 `buildSections(documentId)`，再调用 `getSectionTree(documentId)`。
- 选择章节后调用 `getSectionContent(sectionId)`，中栏展示 `DocumentUnit` 转换出的文本 blocks。
- 生成解析调用 `generateSectionAnalysis(documentId, sectionId)`，右栏展示 markdown 文本。
- 发送追问调用 `sendMessage()`，成功后追加后端返回的 agent 消息。

- [ ] **Step 4: 保留可用 fallback**

实现要点：

- API 请求失败时展示错误状态，不回退到假数据伪装成功。
- 当前 mock 内容可以作为“未选择文档时的空态示例”，但选中文档后必须使用真实 API 数据。
- 不引入全局状态库，继续在 `WorkspacePage` 内部编排。

- [ ] **Step 5: 运行 workspace 测试**

Run: `npm run test:frontend -- src/features/workspace/pages/WorkspacePage.test.tsx`

Expected: PASS。

## Task 5: End-To-End Verification

- [ ] **Step 1: 后端相关测试**

Run: `npm run test:python -- tests/unit/services/test_analysis_service.py tests/unit/services/test_chat_service.py tests/integration/api/test_analysis_controller.py tests/integration/api/test_chat_controller.py -v`

Expected: PASS。

- [ ] **Step 2: 前端相关测试**

Run: `npm run test:frontend -- src/features/workspace/pages/WorkspacePage.test.tsx src/features/document/api src/features/section/api src/features/analysis/api src/features/chat/api`

Expected: PASS。

- [ ] **Step 3: 手动主链路验收**

验收路径：启动后端和前端，上传一个小 PDF，看到文档列表更新；选择文档后看到章节；选择章节后中栏显示原文；点击生成解析后右栏显示解析；发送追问后看到 user 和 agent 消息各一条。

- [ ] **Step 4: 检查提交范围**

Run: `git status --short`

Expected: 只出现本计划涉及的 analysis、chat、workspace、API 封装和测试文件。

- [ ] **Step 5: 分阶段提交**

建议提交：先提交后端 analysis/chat，再提交前端 API layer，再提交 workspace 集成。只暂存本计划涉及的明确文件，不使用全量暂存命令。

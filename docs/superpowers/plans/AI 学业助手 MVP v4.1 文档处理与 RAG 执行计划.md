# AI 学业助手 MVP v4.1 文档处理与 RAG 主链路 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在完全沿用当前仓库框架、目录分层、实体命名和前端 `workspace` 主工作区结构的前提下，完成文档处理与 RAG 主链路闭环：单文件上传 → 文档解析 → 原文持久化 → 章节结构 → Chunk 切块 → Embedding 与检索 → 小节 AI 解析 → 继续追问。

**Architecture:** 前端以 `workspace` 三栏布局为主壳（左栏文件/章节、中栏原文、右栏解析与追问），后端沿用现有 `api → services → repositories → rag → agents` 分层，数据模型保持 `DocumentRecord / DocumentUnit / Section / Chunk / AnalysisResult / ChatSession / ChatMessage` 命名不变。

**Tech Stack:** React 19, TypeScript, Vite 7, Vitest, Tailwind CSS, FastAPI, SQLite, SQLAlchemy, sqlite-vec, Pydantic v2, pytest, OpenAI-compatible provider。

**Design Spec:** `docs/superpowers/specs/2026-06-22-document-rag-current-framework-design.md`

---

## 0. 当前项目判断

### 已有能力

- `backend-python/app/parsers/` 已支持 PDF、DOCX、PPTX、图片、TXT/MD，parser 输出格式已标准化。
- `backend-python/app/services/document_ingest_service.py` 已能解析文件并生成 `DocumentRecord` 和 `DocumentUnit`，但当前仍是内存模式，未持久化。
- `backend-python/app/db/init_db.py` 已有完整表结构和 sqlite-vec 初始化。
- `backend-python/app/repositories/` 已有 `DocumentRepository`、`DocumentUnitRepository`、`SectionRepository`、`ChunkRepository`、`EmbeddingRepository`、`AnalysisResultRepository`、`ChatSessionRepository`、`ChatMessageRepository`。
- `backend-python/app/agents/analysis_agent.py` 已有分析 Agent 雏形。
- `backend-python/app/agents/classification_agent.py` 已有路由分类 Agent。
- `backend-python/app/agents/chat_agent.py` 已有聊天 Agent 雏形（使用 mock 上下文）。
- `backend-python/app/providers/` 已有 `AIProvider` 抽象和 `OpenAICompatibleProvider`，但只有 `chat_completion` 接口，无 embedding 接口。
- `src/features/workspace/` 已有左中右三栏布局骨架，包含 `FileManager`、`SectionTree`、`DocumentViewer`、`ChatPanel`。
- `backend-python/app/schemas/analysis_schema.py` 和 `chat_schema.py` 已有初版请求/响应结构。

### 主要偏差

- `DocumentIngestService` 返回实体但未持久化，需要接入 `UnitOfWork` 和 Repository。
- `SectionService`、`ChunkService`、`ChatService` 仍是占位文件。
- `backend-python/app/main.py` 仅注册了文档上传路由，未注册 section / analysis / chat 路由。
- Provider 抽象缺少 embedding 能力，需要扩展。
- `page_index_builder.py` 和 `retriever.py` 仍是占位。
- 前端 `workspace` 当前使用硬编码 mock 数据，未接入真实 API。
- `document_schema.py`、`section_schema.py` 仍是占位，需要补全。

### 不变的约束

- 不修改现有实体与表名。
- 不把主页面流拆离 `workspace`。
- 不把 chunk 作为中栏正文展示数据源（中栏展示 `DocumentUnit` 原文）。
- 不新建第二套后端主链路命名体系。
- 不把 Tauri 作为业务主逻辑承载层。
- 不把 provider 配置管理、导出、历史恢复混入本次主链路范围。

---

## 1. 文件结构总览

### 后端修改文件

| 文件 | 职责 |
|------|------|
| `backend-python/app/db/connection.py` | 补 DB 引擎、Session 工厂、UOW 工厂 |
| `backend-python/app/main.py` | 注册 section / analysis / chat 路由 |
| `backend-python/app/schemas/document_schema.py` | 补文档上传响应、文档列表、文档详情 schema |
| `backend-python/app/schemas/section_schema.py` | 补章节树、章节原文响应 schema |
| `backend-python/app/services/document_ingest_service.py` | 接入 UOW 持久化 |
| `backend-python/app/services/section_service.py` | 实现章节构建与查询 |
| `backend-python/app/services/chunk_service.py` | 实现 chunk 切分 |
| `backend-python/app/services/embedding_service.py` | 实现 embedding 生成与写入 |
| `backend-python/app/services/analysis_service.py` | 收敛为正式 service |
| `backend-python/app/services/chat_service.py` | 实现会话与追问 |
| `backend-python/app/rag/page_index_builder.py` | 实现 DocumentUnit → Section 结构提取 |
| `backend-python/app/rag/retriever.py` | 实现 chunk 检索 |
| `backend-python/app/api/document_controller.py` | 调整依赖注入，返回持久化结果 |
| `backend-python/app/api/section_controller.py` | 补章节树与章节原文 API |
| `backend-python/app/api/analysis_controller.py` | 补分析生成与查询 API |
| `backend-python/app/api/chat_controller.py` | 补会话与追问 API |
| `backend-python/app/providers/base.py` | 扩展 embedding 接口 |
| `backend-python/app/providers/openai_compat_provider.py` | 实现 OpenAI embedding |

### 后端新增文件

| 文件 | 职责 |
|------|------|
| `backend-python/app/api/dependencies.py` | 集中管理 UOW、Service 依赖注入 |

### 前端修改文件

| 文件 | 职责 |
|------|------|
| `src/features/document/api/documentApi.ts` | 补文档上传、列表 API 封装 |
| `src/features/section/api/sectionApi.ts` | 补章节树、章节原文 API 封装 |
| `src/features/analysis/api/analysisApi.ts` | 补分析生成与查询 API 封装 |
| `src/features/chat/api/chatApi.ts` | 补会话创建、消息发送 API 封装 |
| `src/features/workspace/pages/WorkspacePage.tsx` | 接入真实 API，编排主流程 |
| `src/features/workspace/type.ts` | 补充 workspace 状态类型 |

### 测试文件

| 文件 | 类型 |
|------|------|
| `backend-python/tests/unit/services/test_document_ingest_service.py` | 修改 |
| `backend-python/tests/unit/services/test_section_service.py` | 修改 |
| `backend-python/tests/unit/services/test_chunk_service.py` | 修改 |
| `backend-python/tests/unit/services/test_analysis_service.py` | 修改 |
| `backend-python/tests/unit/providers/test_openai_compat_provider.py` | 修改 |
| `backend-python/tests/integration/api/test_document_controller.py` | 修改 |
| `backend-python/tests/integration/api/test_section_controller.py` | 新增 |
| `backend-python/tests/integration/api/test_chat_controller.py` | 新增 |
| `backend-python/tests/integration/persistence/test_sqlite_repositories.py` | 修改 |
| `src/features/workspace/pages/WorkspacePage.test.tsx` | 修改 |

---

## 2. Task 1: DB Bootstrap & Document Ingest Persistence

**目标:** 把 `DocumentIngestService` 从内存模式升级为持久化模式，通过 `UnitOfWork` 写入 `DocumentRecord` 和 `DocumentUnit`。

**Files:**

- Modify: `backend-python/app/db/connection.py`
- Create: `backend-python/app/api/dependencies.py`
- Modify: `backend-python/app/services/document_ingest_service.py`
- Modify: `backend-python/app/api/document_controller.py`
- Modify: `backend-python/app/schemas/document_schema.py`
- Modify: `backend-python/tests/unit/services/test_document_ingest_service.py`
- Modify: `backend-python/tests/integration/api/test_document_controller.py`

- [ ] **Step 1: Write failing test for DB connection bootstrap**

```python
# backend-python/tests/unit/db/test_connection.py
from app.db.connection import create_app_session_factory, create_app_uow


def test_create_app_session_factory_returns_session_factory():
    session_factory = create_app_session_factory(":memory:", embedding_dimension=8)
    with session_factory() as session:
        assert session is not None


def test_create_app_uow_returns_unit_of_work():
    from app.db.unit_of_work import SqlAlchemyUnitOfWork
    session_factory = create_app_session_factory(":memory:", embedding_dimension=8)
    uow = create_app_uow(session_factory)
    assert isinstance(uow, SqlAlchemyUnitOfWork)
```

Run: `npm run test:python -- tests/unit/db/test_connection.py -v`
Expected: FAIL with "cannot import name 'create_app_session_factory'"

- [ ] **Step 2: Implement DB connection bootstrap**

```python
# backend-python/app/db/connection.py
from pathlib import Path

from app.db.init_db import initialize_database, load_sqlite_vec_extension
from app.db.orm import create_database_engine, create_session_factory, SessionFactory
from app.db.unit_of_work import SqlAlchemyUnitOfWork


def create_app_session_factory(
    database_path: str | Path = "data/greenbean-study-assistant.sqlite3",
    *,
    embedding_dimension: int = 1536,
    sqlite_vec_loader=load_sqlite_vec_extension,
) -> SessionFactory:
    path = Path(database_path)
    if path != Path(":memory:"):
        initialize_database(
            data_dir=path.parent,
            database_name=path.name,
            sqlite_vec_loader=sqlite_vec_loader,
            embedding_dimension=embedding_dimension,
        )
    engine = create_database_engine(path, sqlite_vec_loader=sqlite_vec_loader)
    return create_session_factory(engine)


def create_app_uow(session_factory: SessionFactory) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory)
```

- [ ] **Step 3: Run test to verify it passes**

Run: `npm run test:python -- tests/unit/db/test_connection.py -v`
Expected: PASS

- [ ] **Step 4: Write failing test for DocumentIngestService persistence**

```python
# 在 backend-python/tests/unit/services/test_document_ingest_service.py 中新增
from unittest.mock import MagicMock
from app.entities.document_record import DocumentRecord
from app.entities.document_unit import DocumentUnit


def test_ingest_document_persists_record_and_units():
    mock_doc_repo = MagicMock()
    mock_unit_repo = MagicMock()
    mock_uow = MagicMock()
    mock_uow.__enter__ = MagicMock(return_value=mock_uow)
    mock_uow.__exit__ = MagicMock(return_value=False)

    service = DocumentIngestService(
        document_repository=mock_doc_repo,
        document_unit_repository=mock_unit_repo,
        uow=mock_uow,
    )

    with patch("app.parsers.parser_factory.ParserFactory.get_parser") as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            _make_page(page_number=1, content="Page 1"),
            _make_page(page_number=2, content="Page 2"),
        ]
        mock_get_parser.return_value = mock_parser

        result = service.ingest_document("test.pdf", b"fake content")

    assert mock_doc_repo.save.call_count == 1
    assert mock_unit_repo.save.call_count == 2
    assert mock_uow.commit.call_count == 1
    assert result["document_record"].status == DocumentStatus.PARSED
```

Run: `npm run test:python -- tests/unit/services/test_document_ingest_service.py::test_ingest_document_persists_record_and_units -v`
Expected: FAIL with "unexpected keyword argument 'uow'"

- [ ] **Step 5: Implement DocumentIngestService persistence**

```python
# backend-python/app/services/document_ingest_service.py 关键改动
class DocumentIngestService:
    def __init__(
        self,
        document_repository=None,
        document_unit_repository=None,
        uow=None,
    ):
        self.document_repository = document_repository
        self.document_unit_repository = document_unit_repository
        self.uow = uow

    def ingest_document(self, filename, file_content, **kwargs):
        # ... 现有解析逻辑不变 ...

        if self.uow and self.document_repository and self.document_unit_repository:
            with self.uow as uow:
                self.document_repository.save(document_record)
                for unit in document_units:
                    self.document_unit_repository.save(unit)
                uow.commit()

        return { ... }  # 现有返回结构不变
```

- [ ] **Step 6: Run test to verify it passes**

Run: `npm run test:python -- tests/unit/services/test_document_ingest_service.py -v`
Expected: PASS

- [ ] **Step 7: Implement dependencies and update controller**

```python
# backend-python/app/api/dependencies.py
from app.db.connection import create_app_session_factory, create_app_uow
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.services.document_ingest_service import DocumentIngestService

_session_factory = None


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = create_app_session_factory()
    return _session_factory


def get_ingest_service() -> DocumentIngestService:
    session_factory = get_session_factory()
    uow = create_app_uow(session_factory)
    return DocumentIngestService(
        document_repository=None,  # 在 uow context 内创建
        document_unit_repository=None,
        uow=uow,
    )
```

```python
# backend-python/app/api/document_controller.py 修改依赖注入
from app.api.dependencies import get_ingest_service
# 其余逻辑不变
```

- [ ] **Step 8: Run integration test**

Run: `npm run test:python -- tests/integration/api/test_document_controller.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add backend-python/app/db/connection.py backend-python/app/api/dependencies.py backend-python/app/services/document_ingest_service.py backend-python/app/api/document_controller.py backend-python/tests/
git commit -m "feat: implement document ingest persistence with UOW"
```

---

## 3. Task 2: Document Schema & Upload API Refinement

**目标:** 补全文档相关 schema，让上传接口返回结构化的文档信息，支持文档列表查询。

**Files:**

- Modify: `backend-python/app/schemas/document_schema.py`
- Modify: `backend-python/app/api/document_controller.py`
- Modify: `backend-python/app/repositories/document_repository.py`
- Modify: `backend-python/tests/integration/api/test_document_controller.py`

- [ ] **Step 1: Write failing test for document list endpoint**

```python
# backend-python/tests/integration/api/test_document_controller.py 新增
def test_list_documents_returns_workspace_documents(self):
    self.mock_service.list_documents.return_value = [
        {"id": "doc-1", "title": "Test PDF", "file_type": "pdf", "status": "parsed"},
    ]
    response = self.client.get("/api/documents?workspace_id=workspace_1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "doc-1"
```

Run: `npm run test:python -- tests/integration/api/test_document_controller.py::TestDocumentUpload::test_list_documents_returns_workspace_documents -v`
Expected: FAIL with 404

- [ ] **Step 2: Implement document schema**

```python
# backend-python/app/schemas/document_schema.py
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    id: str
    title: str
    original_filename: str
    file_type: str
    status: str
    page_count: int | None
    created_at: datetime


class DocumentListItem(BaseModel):
    id: str
    title: str
    file_type: str
    status: str
    created_at: datetime


class DocumentListResponse(BaseModel):
    data: list[DocumentListItem]
```

- [ ] **Step 3: Implement document list endpoint**

```python
# backend-python/app/api/document_controller.py 新增
@router.get("/")
async def list_documents(workspace_id: str = ""):
    # 调用 service 或 repository 查询
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test:python -- tests/integration/api/test_document_controller.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend-python/app/schemas/document_schema.py backend-python/app/api/document_controller.py backend-python/tests/
git commit -m "feat: add document list API and response schemas"
```

---

## 4. Task 3: Section Building & Section APIs

**目标:** 实现从 `DocumentUnit` 生成 `Section` 树，提供章节树查询和章节原文加载 API。

**Files:**

- Modify: `backend-python/app/rag/page_index_builder.py`
- Modify: `backend-python/app/services/section_service.py`
- Modify: `backend-python/app/schemas/section_schema.py`
- Modify: `backend-python/app/api/section_controller.py`
- Modify: `backend-python/app/main.py`
- Create: `backend-python/tests/integration/api/test_section_controller.py`
- Modify: `backend-python/tests/unit/services/test_section_service.py`

- [ ] **Step 1: Write failing test for page_index_builder**

```python
# backend-python/tests/unit/rag/test_page_index_builder.py
from app.rag.page_index_builder import build_sections_from_units
from app.entities.document_unit import DocumentUnit


def test_build_sections_from_pdf_units():
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            text_content="Chapter 1 introduction...",
            page_number=1,
            metadata_json={"source_type": "pdf", "headings": [{"level": 1, "text": "Chapter 1"}]},
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=1,
            text_content="Chapter 2 content...",
            page_number=2,
            metadata_json={"source_type": "pdf", "headings": [{"level": 1, "text": "Chapter 2"}]},
        ),
    ]
    sections = build_sections_from_units("doc-1", units)
    assert len(sections) == 2
    assert sections[0].title == "Chapter 1"
    assert sections[0].level == 1
    assert sections[0].start_page == 1
```

Run: `npm run test:python -- tests/unit/rag/test_page_index_builder.py -v`
Expected: FAIL with "cannot import name 'build_sections_from_units'"

- [ ] **Step 2: Implement page_index_builder**

```python
# backend-python/app/rag/page_index_builder.py
from app.entities.section import Section
from app.entities.document_unit import DocumentUnit


def build_sections_from_units(
    document_id: str,
    units: list[DocumentUnit],
) -> list[Section]:
    sections: list[Section] = []
    for unit in units:
        headings = (unit.metadata_json or {}).get("headings", [])
        if headings:
            for heading in headings:
                sections.append(Section(
                    document_id=document_id,
                    title=heading.get("text", "Untitled"),
                    level=heading.get("level", 1),
                    order_index=len(sections),
                    start_page=unit.page_number,
                    end_page=unit.page_number,
                ))
        else:
            sections.append(Section(
                document_id=document_id,
                title=f"Page {unit.page_number or unit.sequence_index + 1}",
                level=1,
                order_index=len(sections),
                start_page=unit.page_number,
                end_page=unit.page_number,
            ))
    return sections
```

- [ ] **Step 3: Run test to verify it passes**

Run: `npm run test:python -- tests/unit/rag/test_page_index_builder.py -v`
Expected: PASS

- [ ] **Step 4: Implement SectionService**

```python
# backend-python/app/services/section_service.py
from app.entities.section import Section
from app.rag.page_index_builder import build_sections_from_units
from app.repositories.section_repository import SectionRepository
from app.repositories.document_unit_repository import DocumentUnitRepository


class SectionService:
    def __init__(
        self,
        section_repository: SectionRepository,
        document_unit_repository: DocumentUnitRepository,
        uow=None,
    ):
        self.section_repository = section_repository
        self.document_unit_repository = document_unit_repository
        self.uow = uow

    def build_sections(self, document_id: str) -> list[Section]:
        units = self.document_unit_repository.list_by_document(document_id)
        sections = build_sections_from_units(document_id, units)
        if self.uow:
            with self.uow as uow:
                for section in sections:
                    self.section_repository.save(section)
                uow.commit()
        return sections

    def get_section_tree(self, document_id: str) -> list[dict]:
        sections = self.section_repository.list_by_document(document_id)
        return self._build_tree(sections)

    def get_section_content(self, section_id: str) -> dict:
        section = self.section_repository.get_by_id(section_id)
        if not section:
            raise ValueError(f"Section not found: {section_id}")
        units = self.document_unit_repository.list_by_document(
            section.document_id
        )
        filtered = [
            u for u in units
            if section.start_page and u.page_number
            and section.start_page <= u.page_number <= (section.end_page or section.start_page)
        ]
        return {"section": section, "units": filtered}

    def _build_tree(self, sections: list[Section]) -> list[dict]:
        # 扁平列表转树形结构
        ...
```

- [ ] **Step 5: Implement section schema and controller**

```python
# backend-python/app/schemas/section_schema.py
from pydantic import BaseModel, Field


class SectionNode(BaseModel):
    id: str
    title: str
    level: int
    order_index: int
    start_page: int | None
    end_page: int | None
    children: list["SectionNode"] = []


class SectionTreeResponse(BaseModel):
    document_id: str
    sections: list[SectionNode]


class SectionContentResponse(BaseModel):
    section_id: str
    title: str
    content_blocks: list[dict]
```

```python
# backend-python/app/api/section_controller.py
from fastapi import APIRouter, HTTPException
from app.api.dependencies import get_section_service

router = APIRouter(prefix="/sections", tags=["Sections"])


@router.get("/documents/{document_id}/tree")
async def get_section_tree(document_id: str):
    service = get_section_service()
    tree = service.get_section_tree(document_id)
    return {"document_id": document_id, "sections": tree}


@router.get("/{section_id}/content")
async def get_section_content(section_id: str):
    service = get_section_service()
    try:
        content = service.get_section_content(section_id)
        return content
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

- [ ] **Step 6: Register routes in main.py**

```python
# backend-python/app/main.py
from app.api import document_controller, section_controller, analysis_controller, chat_controller

app = FastAPI(title="Greenbean Study Assistant API")
app.include_router(document_controller.router, prefix="/api")
app.include_router(section_controller.router, prefix="/api")
app.include_router(analysis_controller.router, prefix="/api")
app.include_router(chat_controller.router, prefix="/api")
```

- [ ] **Step 7: Run all section tests**

Run: `npm run test:python -- tests/unit/rag/ tests/unit/services/test_section_service.py tests/integration/api/test_section_controller.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend-python/app/rag/page_index_builder.py backend-python/app/services/section_service.py backend-python/app/schemas/section_schema.py backend-python/app/api/section_controller.py backend-python/app/main.py backend-python/tests/
git commit -m "feat: implement section building and section APIs"
```

---

## 5. Task 4: Chunk Generation & Embedding Provider Extension

**目标:** 实现 chunk 切分，扩展 provider embedding 接口，实现 embedding 生成与写入，实现 retriever。

**Files:**

- Modify: `backend-python/app/services/chunk_service.py`
- Modify: `backend-python/app/providers/base.py`
- Modify: `backend-python/app/providers/openai_compat_provider.py`
- Modify: `backend-python/app/services/embedding_service.py`
- Modify: `backend-python/app/rag/retriever.py`
- Modify: `backend-python/tests/unit/providers/test_openai_compat_provider.py`
- Modify: `backend-python/tests/unit/services/test_chunk_service.py`

- [ ] **Step 1: Write failing test for ChunkService**

```python
# backend-python/tests/unit/services/test_chunk_service.py
from app.services.chunk_service import ChunkService
from app.entities.document_unit import DocumentUnit


def test_chunk_service_splits_units_into_chunks():
    service = ChunkService(max_chunk_size=100)
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            text_content="This is a test document with enough content to be split into multiple chunks. " * 5,
            page_number=1,
        ),
    ]
    chunks = service.split_units_into_chunks(units)
    assert len(chunks) > 0
    assert all(c.text_content for c in chunks)
    assert all(c.document_unit_id == units[0].id for c in chunks)
```

Run: `npm run test:python -- tests/unit/services/test_chunk_service.py -v`
Expected: FAIL with "cannot import name 'ChunkService'"

- [ ] **Step 2: Implement ChunkService**

```python
# backend-python/app/services/chunk_service.py
from app.entities.chunk import Chunk
from app.entities.document_unit import DocumentUnit


class ChunkService:
    def __init__(self, max_chunk_size: int = 500, overlap: int = 50):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def split_units_into_chunks(self, units: list[DocumentUnit]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for unit in units:
            text = unit.text_content
            if len(text) <= self.max_chunk_size:
                chunks.append(Chunk(
                    document_unit_id=unit.id,
                    sequence_index=0,
                    text_content=text,
                    start_char=0,
                    end_char=len(text),
                ))
            else:
                start = 0
                seq = 0
                while start < len(text):
                    end = min(start + self.max_chunk_size, len(text))
                    chunk_text = text[start:end]
                    chunks.append(Chunk(
                        document_unit_id=unit.id,
                        sequence_index=seq,
                        text_content=chunk_text,
                        start_char=start,
                        end_char=end,
                    ))
                    start += self.max_chunk_size - self.overlap
                    seq += 1
        return chunks
```

- [ ] **Step 3: Run test to verify it passes**

Run: `npm run test:python -- tests/unit/services/test_chunk_service.py -v`
Expected: PASS

- [ ] **Step 4: Write failing test for provider embedding interface**

```python
# backend-python/tests/unit/providers/test_openai_compat_provider.py 新增
@pytest.mark.asyncio
async def test_embedding_returns_vector(self, MockAsyncOpenAI, provider_config_factory):
    mock_client = MockAsyncOpenAI.return_value
    mock_response = AsyncMock()
    mock_response.data = [AsyncMock(embedding=[0.1, 0.2, 0.3])]
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)

    provider = OpenAICompatibleProvider(provider_config_factory())
    result = await provider.create_embedding(input="test text")
    assert isinstance(result, EmbeddingResult)
    assert len(result.embedding) == 3
```

Run: `npm run test:python -- tests/unit/providers/test_openai_compat_provider.py::test_embedding_returns_vector -v`
Expected: FAIL with "EmbeddingResult not defined"

- [ ] **Step 5: Implement provider embedding interface**

```python
# backend-python/app/providers/base.py 新增
class EmbeddingResult:
    def __init__(self, embedding: list[float], model: str) -> None:
        self.embedding = embedding
        self.model = model


class AIProvider(ABC):
    @abstractmethod
    async def chat_completion(self, ...) -> ChatResult:
        ...

    async def create_embedding(
        self,
        input: str | list[str],
        model: str | None = None,
    ) -> EmbeddingResult:
        raise NotImplementedError("This provider does not support embeddings")
```

```python
# backend-python/app/providers/openai_compat_provider.py 新增
async def create_embedding(
    self,
    input: str | list[str],
    model: str | None = None,
) -> EmbeddingResult:
    response = await self._client.embeddings.create(
        model=model or self.config.embedding_model_id,
        input=input,
    )
    return EmbeddingResult(
        embedding=response.data[0].embedding,
        model=response.model,
    )
```

- [ ] **Step 6: Run test to verify it passes**

Run: `npm run test:python -- tests/unit/providers/test_openai_compat_provider.py -v`
Expected: PASS

- [ ] **Step 7: Implement EmbeddingService and Retriever**

```python
# backend-python/app/services/embedding_service.py
from app.providers.registry import ProviderRegistry
from app.repositories.embedding_repository import EmbeddingRepository


class EmbeddingService:
    def __init__(self, embedding_repository: EmbeddingRepository):
        self.embedding_repository = embedding_repository

    async def embed_chunks(self, chunk_ids: list[str], texts: list[str], model: str):
        provider = ProviderRegistry.get_active()
        result = await provider.create_embedding(input=texts)
        for chunk_id, vector in zip(chunk_ids, result.embedding):
            self.embedding_repository.save_for_chunk(
                chunk_id=chunk_id,
                embedding_model=result.model,
                vector=vector,
            )
```

```python
# backend-python/app/rag/retriever.py
from app.repositories.embedding_repository import EmbeddingRepository


class Retriever:
    def __init__(self, embedding_repository: EmbeddingRepository):
        self.embedding_repository = embedding_repository

    def retrieve(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        # 简化版：遍历比较余弦相似度
        # 后续可优化为 sqlite-vec 向量检索
        ...
```

- [ ] **Step 8: Commit**

```bash
git add backend-python/app/services/chunk_service.py backend-python/app/providers/base.py backend-python/app/providers/openai_compat_provider.py backend-python/app/services/embedding_service.py backend-python/app/rag/retriever.py backend-python/tests/
git commit -m "feat: implement chunk service and embedding provider extension"
```

---

## 6. Task 5: Analysis Service & Workspace Integration

**目标:** 把 `analysis_service.py` 从演示函数收敛为正式 service，接入真实上下文，提供分析 API。

**Files:**

- Modify: `backend-python/app/services/analysis_service.py`
- Modify: `backend-python/app/api/analysis_controller.py`
- Modify: `backend-python/app/main.py`

- [ ] **Step 1: Write failing test for AnalysisService**

```python
# backend-python/tests/unit/services/test_analysis_service.py 新增
@pytest.mark.asyncio
async def test_analysis_service_returns_existing_result():
    mock_repo = MagicMock()
    mock_repo.get_by_section_id.return_value = AnalysisResult(
        document_id="doc-1",
        section_id="sec-1",
        analysis_type=AnalysisType.SECTION,
        language="zh",
        content_markdown="已有解析",
    )
    service = AnalysisService(analysis_repository=mock_repo)
    result = await service.get_or_create_analysis("doc-1", "sec-1", "context")
    assert result.content_markdown == "已有解析"
    assert mock_repo.save.call_count == 0  # 不重复创建
```

Run: `npm run test:python -- tests/unit/services/test_analysis_service.py -v`
Expected: FAIL

- [ ] **Step 2: Implement AnalysisService**

```python
# backend-python/app/services/analysis_service.py
from app.entities.analysis_result import AnalysisResult
from app.enums.analysis_type import AnalysisType
from app.agents.analysis_agent import AnalysisAgent
from app.repositories.analysis_result_repository import AnalysisResultRepository


class AnalysisService:
    def __init__(
        self,
        analysis_repository: AnalysisResultRepository,
        analysis_agent: AnalysisAgent | None = None,
        uow=None,
    ):
        self.analysis_repository = analysis_repository
        self.analysis_agent = analysis_agent or AnalysisAgent()
        self.uow = uow

    async def get_or_create_analysis(
        self,
        document_id: str,
        section_id: str,
        context: str,
    ) -> AnalysisResult:
        existing = self.analysis_repository.get_by_section_id(section_id)
        if existing:
            return existing

        raw_json = await self.analysis_agent.generate_analysis(context)
        markdown = build_markdown_from_json(raw_json)
        result = AnalysisResult(
            document_id=document_id,
            section_id=section_id,
            analysis_type=AnalysisType.SECTION,
            language="zh",
            content_markdown=markdown,
            content_json=raw_json,
        )

        if self.uow:
            with self.uow as uow:
                self.analysis_repository.save(result)
                uow.commit()

        return result
```

- [ ] **Step 3: Implement analysis controller**

```python
# backend-python/app/api/analysis_controller.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.api.dependencies import get_analysis_service

router = APIRouter(prefix="/analysis", tags=["Analysis"])


class AnalysisRequest(BaseModel):
    document_id: str
    section_id: str


@router.post("/generate")
async def generate_analysis(request: AnalysisRequest):
    service = get_analysis_service()
    # 获取 section 原文作为 context
    context = "..."  # 从 section service 获取
    result = await service.get_or_create_analysis(
        request.document_id, request.section_id, context
    )
    return {
        "id": result.id,
        "section_id": result.section_id,
        "content_markdown": result.content_markdown,
        "content_json": result.content_json,
    }
```

- [ ] **Step 4: Run tests**

Run: `npm run test:python -- tests/unit/services/test_analysis_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend-python/app/services/analysis_service.py backend-python/app/api/analysis_controller.py backend-python/tests/
git commit -m "feat: implement analysis service with section context"
```

---

## 7. Task 6: Chat Service & Workspace Integration

**目标:** 实现 `ChatService`，接入路由分类、RAG 检索和会话持久化，提供聊天 API。

**Files:**

- Modify: `backend-python/app/services/chat_service.py`
- Modify: `backend-python/app/agents/chat_agent.py`
- Modify: `backend-python/app/api/chat_controller.py`
- Modify: `backend-python/app/main.py`

- [ ] **Step 1: Write failing test for ChatService**

```python
# backend-python/tests/unit/services/test_chat_service.py
@pytest.mark.asyncio
async def test_chat_service_creates_session_and_message():
    mock_session_repo = MagicMock()
    mock_message_repo = MagicMock()
    mock_chat_agent = AsyncMock()
    mock_chat_agent.generate_response.return_value = ChatResponse(
        session_id="test-session",
        answer="测试回复",
    )
    service = ChatService(
        session_repository=mock_session_repo,
        message_repository=mock_message_repo,
        chat_agent=mock_chat_agent,
    )

    response = await service.send_message(
        workspace_id="ws-1",
        document_id="doc-1",
        session_id=None,  # 新建会话
        query="测试问题",
    )

    assert response.answer == "测试回复"
    assert mock_session_repo.save.call_count == 1
    assert mock_message_repo.save.call_count == 2  # user + agent
```

Run: `npm run test:python -- tests/unit/services/test_chat_service.py -v`
Expected: FAIL

- [ ] **Step 2: Implement ChatService**

```python
# backend-python/app/services/chat_service.py
from app.entities.chat_session import ChatSession
from app.entities.chat_message import ChatMessage
from app.enums.message_role import MessageRole
from app.agents.chat_agent import ChatAgent
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.schemas.chat_schema import ChatRequest, ChatResponse


class ChatService:
    def __init__(
        self,
        session_repository: ChatSessionRepository,
        message_repository: ChatMessageRepository,
        chat_agent: ChatAgent | None = None,
        uow=None,
    ):
        self.session_repository = session_repository
        self.message_repository = message_repository
        self.chat_agent = chat_agent or ChatAgent()
        self.uow = uow

    async def send_message(
        self,
        workspace_id: str,
        document_id: str | None,
        session_id: str | None,
        query: str,
        section_id: str | None = None,
    ) -> ChatResponse:
        # 获取或创建会话
        if session_id:
            session = self.session_repository.get_by_id(session_id)
        else:
            session = ChatSession(
                workspace_id=workspace_id,
                document_id=document_id,
                title=query[:50],
            )
            if self.uow:
                with self.uow as uow:
                    self.session_repository.save(session)
                    uow.commit()

        # 保存用户消息
        user_message = ChatMessage(
            session_id=session.id,
            role=MessageRole.USER,
            content=query,
        )

        # 获取历史消息
        history = self.message_repository.list_by_session(session.id)

        # 构建请求
        request = ChatRequest(
            session_id=session.id,
            query=query,
            history=[{"role": m.role.value, "content": m.content} for m in history],
        )

        # 调用 Agent
        response = await self.chat_agent.generate_response(request)

        # 保存 Agent 回复
        agent_message = ChatMessage(
            session_id=session.id,
            role=MessageRole.AGENT,
            content=response.answer,
            source_context_json=response.source_context,
        )

        if self.uow:
            with self.uow as uow:
                self.message_repository.save(user_message)
                self.message_repository.save(agent_message)
                uow.commit()

        return response
```

- [ ] **Step 3: Implement chat controller**

```python
# backend-python/app/api/chat_controller.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.api.dependencies import get_chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatMessageRequest(BaseModel):
    workspace_id: str
    document_id: str | None = None
    session_id: str | None = None
    query: str
    section_id: str | None = None


@router.post("/messages")
async def send_message(request: ChatMessageRequest):
    service = get_chat_service()
    response = await service.send_message(
        workspace_id=request.workspace_id,
        document_id=request.document_id,
        session_id=request.session_id,
        query=request.query,
        section_id=request.section_id,
    )
    return response
```

- [ ] **Step 4: Run tests**

Run: `npm run test:python -- tests/unit/services/test_chat_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend-python/app/services/chat_service.py backend-python/app/agents/chat_agent.py backend-python/app/api/chat_controller.py backend-python/tests/
git commit -m "feat: implement chat service with session persistence"
```

---

## 8. Task 7: Frontend Workspace Integration

**目标:** 把 `workspace` 从硬编码 mock 数据改为接入真实后端 API，完成主链路前端闭环。

**Files:**

- Modify: `src/features/document/api/documentApi.ts`
- Modify: `src/features/section/api/sectionApi.ts`
- Modify: `src/features/analysis/api/analysisApi.ts`
- Modify: `src/features/chat/api/chatApi.ts`
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`
- Modify: `src/features/workspace/type.ts`
- Modify: `src/features/workspace/pages/WorkspacePage.test.tsx`

- [ ] **Step 1: Implement documentApi.ts**

```typescript
// src/features/document/api/documentApi.ts
const API_BASE = "http://localhost:8000/api";

export interface DocumentUploadResult {
  id: string;
  title: string;
  original_filename: string;
  file_type: string;
  status: string;
  page_count: number | null;
}

export async function uploadDocument(file: File): Promise<DocumentUploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "上传失败");
  }
  const data = await response.json();
  return data.data;
}

export async function listDocuments(workspaceId: string) {
  const response = await fetch(`${API_BASE}/documents?workspace_id=${workspaceId}`);
  const data = await response.json();
  return data.data;
}
```

- [ ] **Step 2: Implement sectionApi.ts**

```typescript
// src/features/section/api/sectionApi.ts
export interface SectionNode {
  id: string;
  title: string;
  level: number;
  children?: SectionNode[];
}

export async function getSectionTree(documentId: string): Promise<SectionNode[]> {
  const response = await fetch(`${API_BASE}/sections/documents/${documentId}/tree`);
  const data = await response.json();
  return data.sections;
}

export async function getSectionContent(sectionId: string) {
  const response = await fetch(`${API_BASE}/sections/${sectionId}/content`);
  return response.json();
}
```

- [ ] **Step 3: Implement analysisApi.ts and chatApi.ts**

```typescript
// src/features/analysis/api/analysisApi.ts
export async function generateAnalysis(documentId: string, sectionId: string) {
  const response = await fetch(`${API_BASE}/analysis/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, section_id: sectionId }),
  });
  return response.json();
}
```

```typescript
// src/features/chat/api/chatApi.ts
export async function sendMessage(request: {
  workspace_id: string;
  document_id?: string;
  session_id?: string;
  query: string;
  section_id?: string;
}) {
  const response = await fetch(`${API_BASE}/chat/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  return response.json();
}
```

- [ ] **Step 4: Update WorkspacePage.tsx to use real APIs**

关键改动点：
- `FileManager` 的 `files` 从 API 获取而非硬编码
- 选择文件后调用 `getSectionTree` 获取章节树
- 选择章节后调用 `getSectionContent` 获取原文
- 右栏 `ChatPanel` 的 `onSend` 调用 `sendMessage`
- 新增解析触发按钮调用 `generateAnalysis`

- [ ] **Step 5: Run frontend tests**

Run: `npm run test:frontend`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/features/ src/features/workspace/
git commit -m "feat: integrate workspace with real backend APIs"
```

---

## 9. Task 8: End-to-End Verification

**目标:** 验证主链路闭环，确保所有 Phase 贯通。

- [ ] **Step 1: Run all Python tests**

Run: `npm run test:python`
Expected: PASS

- [ ] **Step 2: Run all frontend tests**

Run: `npm run test:frontend`
Expected: PASS

- [ ] **Step 3: Manual E2E verification checklist**

- [ ] 上传 PDF → 文档写入 `document_records`
- [ ] `document_units` 按页写入
- [ ] `sections` 生成章节树
- [ ] 前端左栏展示章节树
- [ ] 点击章节，中栏加载原文
- [ ] 生成 chunks 和 embeddings
- [ ] 点击生成解析 → `analysis_results` 写入
- [ ] 追问问题 → `chat_sessions` 和 `chat_messages` 写入
- [ ] 关闭重开后数据可恢复

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete document processing and RAG main pipeline"
```

---

## 10. 推荐执行顺序

1. **Task 1:** DB Bootstrap & Document Ingest Persistence
2. **Task 2:** Document Schema & Upload API Refinement
3. **Task 3:** Section Building & Section APIs
4. **Task 4:** Chunk Generation & Embedding Provider Extension
5. **Task 5:** Analysis Service & Workspace Integration
6. **Task 6:** Chat Service & Workspace Integration
7. **Task 7:** Frontend Workspace Integration
8. **Task 8:** End-to-End Verification

原因：先稳定数据持久化（Task 1-2），再构建结构化索引（Task 3），然后补齐 RAG 能力（Task 4），最后串 AI 分析和追问（Task 5-6），前端集成（Task 7）和验证（Task 8）收尾。

---

## 11. 风险与处理

### Provider embedding 接口缺失

当前 `AIProvider` 只有 `chat_completion`，无 `create_embedding`。

处理：Task 4 扩展 `AIProvider` 抽象和 `OpenAICompatibleProvider`，添加 `create_embedding` 方法。

### sqlite-vec 环境风险

sqlite-vec 需要扩展加载能力，Windows 环境可能需要明确动态库路径。

处理：`db/orm.py` 已有 `sqlite_vec_loader` 机制，集成测试使用 mock loader。

### 文档状态推进

`DocumentStatus` 只有 `uploaded/parsed/indexed/failed`，不新增 `processing` 等中间态。

处理：中间过程态仅作为 API 临时响应字段，不写入数据库。

### 前端 mock 数据迁移

当前 `WorkspacePage` 使用硬编码 mock 数据，迁移需要逐步替换。

处理：Task 7 先替换核心流程，保留非主链路功能的 mock 数据。

---

## 12. 每阶段完成标准

每个 Task 必须满足：

- [ ] 有单元测试覆盖核心逻辑。
- [ ] 有至少一个集成测试覆盖 API 或持久化。
- [ ] 不引入与现有命名冲突的数据模型。
- [ ] chunks 只存原文，不存 AI 生成内容。
- [ ] 首次解析不读取 analyses/chat_messages。
- [ ] 追问默认上下文只含原文 chunks + 当前会话历史。
- [ ] `npm run test:python` 通过。
- [ ] 涉及前端时 `npm run test:frontend` 通过。

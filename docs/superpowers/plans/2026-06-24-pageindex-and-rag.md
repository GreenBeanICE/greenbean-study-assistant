# PageIndex And Rag Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为已解析文档补齐最小可工作的 `PageIndex + RAG` 后端主链路，包括章节构建、章节内容 API、chunk 切分、embedding 持久化与最小检索。

**Architecture:** 保持现有 `entity -> repository -> service -> api` 分层，不做跨层捷径。`rag/` 只放纯规则和检索逻辑，事务统一由 service 层或测试中的 session/UOW 控制；检索阶段先使用 Python 余弦相似度，避免引入 `sqlite-vec` 作为本次交付前置条件。

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy, SQLite, pytest, unittest.mock, OpenAI SDK

---

## File Map

- Create: `backend-python/app/repositories/section_unit_link_repository.py`
  - 持久化 `SectionUnitLink`，提供 `save()`、`list_by_section()`。
- Modify: `backend-python/app/db/models.py`
  - 增加 `SectionUnitLinkModel`，为 `sections` 增加 `(document_id, order_index)` 唯一约束。
- Modify: `backend-python/app/db/init_db.py`
  - 建 `section_unit_links` 表，补 `sections(document_id, order_index)` 唯一约束。
- Modify: `backend-python/app/repositories/section_repository.py`
  - 增加 `list_by_document()`，统一 `_to_entity()`。
- Modify: `backend-python/app/repositories/document_unit_repository.py`
  - 增加 `list_by_ids(unit_ids)`，保持输入顺序。
- Modify: `backend-python/app/repositories/chunk_repository.py`
  - 增加 `list_by_document(document_id)` 和 `list_by_ids(ids)`。
- Modify: `backend-python/app/repositories/embedding_repository.py`
  - 增加 `list_by_document(document_id)`。
- Modify: `backend-python/app/rag/page_index_builder.py`
  - 实现 `build_sections_from_units(document_id, units)`。
- Modify: `backend-python/app/rag/retriever.py`
  - 实现 `Retriever` 和最小检索结果结构。
- Modify: `backend-python/app/services/section_service.py`
  - 编排 section 构建、树转换、章节内容查询。
- Modify: `backend-python/app/services/chunk_service.py`
  - 实现 chunk 切分与持久化入口。
- Modify: `backend-python/app/services/embedding_service.py`
  - 实现 provider embedding 调用、数量校验与原子写入。
- Modify: `backend-python/app/providers/base.py`
  - 增加 `EmbeddingResult` 和 `create_embedding()` 抽象。
- Modify: `backend-python/app/providers/openai_compat_provider.py`
  - 实现 OpenAI-compatible embeddings 调用。
- Modify: `backend-python/app/api/dependencies.py`
  - 增加 `get_section_service()`。
- Modify: `backend-python/app/schemas/section_schema.py`
  - 定义 build/tree/content 响应结构。
- Modify: `backend-python/app/api/section_controller.py`
  - 暴露 `build/tree/content` 三个路由。
- Modify: `backend-python/app/main.py`
  - 注册 `section_controller.router`。
- Create: `backend-python/tests/unit/rag/test_page_index_builder.py`
  - 覆盖 headings、page fallback、empty input。
- Create: `backend-python/tests/integration/persistence/test_section_unit_link_repository.py`
  - 覆盖 schema、唯一约束和排序查询。
- Modify: `backend-python/tests/unit/services/test_section_service.py`
  - 覆盖幂等构建、树输出、link 内容读取、404 场景。
- Create: `backend-python/tests/integration/api/test_section_controller.py`
  - 覆盖 build/tree/content 成功与 404。
- Modify: `backend-python/tests/unit/services/test_chunk_service.py`
  - 覆盖 chunk 窗口切分、空白跳过、构造参数校验、文档持久化。
- Create: `backend-python/tests/unit/services/test_embedding_service.py`
  - 覆盖数量不匹配回滚、成功写入。
- Modify: `backend-python/tests/unit/providers/test_openai_compat_provider.py`
  - 增加 embedding 单条和多条调用测试。
- Create: `backend-python/tests/unit/rag/test_retriever.py`
  - 覆盖排序、空索引、维度不一致跳过。

### Task 1: 实现 PageIndex Builder

**Files:**
- Modify: `backend-python/app/rag/page_index_builder.py`
- Test: `backend-python/tests/unit/rag/test_page_index_builder.py`

- [ ] **Step 1: 写失败测试，覆盖 headings、页码回退和空输入**

```python
import pytest

from app.entities import DocumentUnit
from app.rag.page_index_builder import build_sections_from_units


def test_build_sections_prefers_heading_metadata():
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=3,
            text_content="Unit text",
            metadata_json={"headings": [{"title": "Chapter 1", "level": 1}]},
        )
    ]

    sections = build_sections_from_units("doc-1", units)

    assert len(sections) == 1
    assert sections[0].title == "Chapter 1"
    assert sections[0].level == 1
    assert sections[0].order_index == 0
    assert sections[0].start_page == 3
    assert sections[0].end_page == 3


def test_build_sections_falls_back_to_page_number_or_sequence():
    units = [
        DocumentUnit(document_id="doc-1", sequence_index=0, page_number=2, text_content="Page unit"),
        DocumentUnit(document_id="doc-1", sequence_index=1, text_content="No page unit"),
    ]

    sections = build_sections_from_units("doc-1", units)

    assert [section.title for section in sections] == ["Page 2", "Unit 2"]
    assert [section.level for section in sections] == [1, 1]


def test_build_sections_returns_empty_for_empty_units():
    assert build_sections_from_units("doc-1", []) == []
```

- [ ] **Step 2: 运行测试确认当前实现失败**

Run: `npm run test:python -- tests/unit/rag/test_page_index_builder.py -v`

Expected: FAIL，报 `ImportError` 或 `build_sections_from_units` 未定义。

- [ ] **Step 3: 写最小实现**

```python
from app.entities import DocumentUnit, Section


def build_sections_from_units(document_id: str, units: list[DocumentUnit]) -> list[Section]:
    sections: list[Section] = []
    for unit in units:
        headings = (unit.metadata_json or {}).get("headings") or []
        if headings:
            heading = headings[0]
            title = heading.get("title") or f"Page {unit.page_number}" if unit.page_number else f"Unit {unit.sequence_index + 1}"
            level = int(heading.get("level") or 1)
        else:
            title = f"Page {unit.page_number}" if unit.page_number is not None else f"Unit {unit.sequence_index + 1}"
            level = 1

        sections.append(
            Section(
                document_id=document_id,
                title=title,
                level=level,
                order_index=len(sections),
                start_page=unit.page_number,
                end_page=unit.page_number,
                metadata_json={"source_unit_id": unit.id},
            )
        )
    return sections
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test:python -- tests/unit/rag/test_page_index_builder.py -v`

Expected: PASS。

### Task 2: 补齐 SectionUnitLink 持久化

**Files:**
- Modify: `backend-python/app/db/models.py`
- Modify: `backend-python/app/db/init_db.py`
- Create: `backend-python/app/repositories/section_unit_link_repository.py`
- Test: `backend-python/tests/integration/persistence/test_section_unit_link_repository.py`

- [ ] **Step 1: 写失败集成测试，覆盖建表、唯一约束和排序读取**

```python
import sqlite3

import pytest

from app.db.init_db import initialize_database
from app.db.orm import create_database_engine, create_session_factory
from app.entities import DocumentRecord, DocumentUnit, Section, SectionUnitLink
from app.enums import DocumentFileType
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.repositories.section_repository import SectionRepository
from app.repositories.section_unit_link_repository import SectionUnitLinkRepository


def _load_test_sqlite_vec(connection: sqlite3.Connection) -> None:
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def test_section_unit_link_repository_saves_and_lists_in_order(tmp_path):
    result = initialize_database(
        data_dir=tmp_path / "data",
        sqlite_vec_loader=_load_test_sqlite_vec,
        embedding_dimension=8,
    )
    engine = create_database_engine(result.database_path, sqlite_vec_loader=_load_test_sqlite_vec)
    session_factory = create_session_factory(engine)

    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit_a = DocumentUnit(document_id=document.id, sequence_index=0, text_content="A")
    unit_b = DocumentUnit(document_id=document.id, sequence_index=1, text_content="B")
    section = Section(document_id=document.id, title="Section 1", level=1, order_index=0)

    with session_factory() as session:
        DocumentRepository(session).save(document)
        DocumentUnitRepository(session).save(unit_a)
        DocumentUnitRepository(session).save(unit_b)
        SectionRepository(session).save(section)
        repo = SectionUnitLinkRepository(session)
        repo.save(SectionUnitLink(section_id=section.id, document_unit_id=unit_b.id, order_index=1))
        repo.save(SectionUnitLink(section_id=section.id, document_unit_id=unit_a.id, order_index=0))
        session.commit()

    with session_factory() as session:
        links = SectionUnitLinkRepository(session).list_by_section(section.id)

    engine.dispose()
    assert [link.document_unit_id for link in links] == [unit_a.id, unit_b.id]


def test_section_unit_link_repository_enforces_uniqueness(tmp_path):
    result = initialize_database(
        data_dir=tmp_path / "data",
        sqlite_vec_loader=_load_test_sqlite_vec,
        embedding_dimension=8,
    )
    engine = create_database_engine(result.database_path, sqlite_vec_loader=_load_test_sqlite_vec)
    session_factory = create_session_factory(engine)

    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit = DocumentUnit(document_id=document.id, sequence_index=0, text_content="A")
    section = Section(document_id=document.id, title="Section 1", level=1, order_index=0)

    with session_factory() as session:
        DocumentRepository(session).save(document)
        DocumentUnitRepository(session).save(unit)
        SectionRepository(session).save(section)
        repo = SectionUnitLinkRepository(session)
        repo.save(SectionUnitLink(section_id=section.id, document_unit_id=unit.id, order_index=0))
        session.commit()

    with pytest.raises(Exception):
        with session_factory() as session:
            SectionUnitLinkRepository(session).save(
                SectionUnitLink(section_id=section.id, document_unit_id=unit.id, order_index=1)
            )
            session.commit()

    engine.dispose()
```

- [ ] **Step 2: 运行测试确认当前实现失败**

Run: `npm run test:python -- tests/integration/persistence/test_section_unit_link_repository.py -v`

Expected: FAIL，报 `ModuleNotFoundError` 或 `section_unit_links` 表不存在。

- [ ] **Step 3: 在 schema 和 model 中增加最小持久化结构**

```python
class SectionModel(Base):
    __tablename__ = "sections"
    __table_args__ = (UniqueConstraint("document_id", "order_index"),)


class SectionUnitLinkModel(Base):
    __tablename__ = "section_unit_links"
    __table_args__ = (
        UniqueConstraint("section_id", "document_unit_id"),
        UniqueConstraint("section_id", "order_index"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    section_id: Mapped[str] = mapped_column(ForeignKey("sections.id"), nullable=False)
    document_unit_id: Mapped[str] = mapped_column(ForeignKey("document_units.id"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
```

```python
CREATE TABLE IF NOT EXISTS section_unit_links (
    id TEXT PRIMARY KEY,
    section_id TEXT NOT NULL,
    document_unit_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    FOREIGN KEY (section_id) REFERENCES sections(id),
    FOREIGN KEY (document_unit_id) REFERENCES document_units(id),
    UNIQUE (section_id, document_unit_id),
    UNIQUE (section_id, order_index)
);
```

- [ ] **Step 4: 实现 `SectionUnitLinkRepository`**

```python
from sqlalchemy.orm import Session

from app.db.models import SectionUnitLinkModel
from app.entities import SectionUnitLink


class SectionUnitLinkRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, link: SectionUnitLink) -> SectionUnitLink:
        model = self.session.get(SectionUnitLinkModel, link.id)
        if model is None:
            model = SectionUnitLinkModel(id=link.id)
            self.session.add(model)
        model.section_id = link.section_id
        model.document_unit_id = link.document_unit_id
        model.order_index = link.order_index
        return link

    def list_by_section(self, section_id: str) -> list[SectionUnitLink]:
        models = (
            self.session.query(SectionUnitLinkModel)
            .filter(SectionUnitLinkModel.section_id == section_id)
            .order_by(SectionUnitLinkModel.order_index)
            .all()
        )
        return [
            SectionUnitLink(
                id=model.id,
                section_id=model.section_id,
                document_unit_id=model.document_unit_id,
                order_index=model.order_index,
            )
            for model in models
        ]
```

- [ ] **Step 5: 运行测试确认通过**

Run: `npm run test:python -- tests/integration/persistence/test_section_unit_link_repository.py -v`

Expected: PASS。

### Task 3: 实现 SectionService 和 Section API

**Files:**
- Modify: `backend-python/app/services/section_service.py`
- Modify: `backend-python/app/repositories/section_repository.py`
- Modify: `backend-python/app/repositories/document_unit_repository.py`
- Modify: `backend-python/app/api/dependencies.py`
- Modify: `backend-python/app/schemas/section_schema.py`
- Modify: `backend-python/app/api/section_controller.py`
- Modify: `backend-python/app/main.py`
- Test: `backend-python/tests/unit/services/test_section_service.py`
- Test: `backend-python/tests/integration/api/test_section_controller.py`

- [ ] **Step 1: 写失败测试，先约束 service 幂等、树和内容读取**

```python
import sqlite3

import pytest

from app.db.connection import create_app_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.entities import DocumentRecord, DocumentUnit, Section
from app.enums import DocumentFileType
from app.services.section_service import SectionService


def _fake_sqlite_vec_loader(connection):
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


@pytest.fixture
def uow_factory(tmp_path):
    database_path = tmp_path / "data" / "section.sqlite3"
    session_factory = create_app_session_factory(
        database_path=database_path,
        embedding_dimension=8,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )
    return lambda: SqlAlchemyUnitOfWork(session_factory)


def test_build_sections_returns_existing_sections_without_rebuilding(uow_factory):
    from app.repositories.document_repository import DocumentRepository
    from app.repositories.document_unit_repository import DocumentUnitRepository
    from app.repositories.section_repository import SectionRepository

    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit = DocumentUnit(document_id=document.id, sequence_index=0, page_number=1, text_content="Text")
    existing = Section(document_id=document.id, title="Existing", level=1, order_index=0)

    with uow_factory() as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(unit)
        SectionRepository(uow.session).save(existing)
        uow.commit()

    service = SectionService(uow_factory=uow_factory)
    sections = service.build_sections(document.id)

    assert len(sections) == 1
    assert sections[0].title == "Existing"


def test_get_section_tree_returns_nested_nodes(uow_factory):
    from app.repositories.document_repository import DocumentRepository
    from app.repositories.section_repository import SectionRepository

    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    root = Section(document_id=document.id, title="Root", level=1, order_index=0)
    child = Section(document_id=document.id, parent_section_id=root.id, title="Child", level=2, order_index=1)

    with uow_factory() as uow:
        DocumentRepository(uow.session).save(document)
        SectionRepository(uow.session).save(root)
        SectionRepository(uow.session).save(child)
        uow.commit()

    service = SectionService(uow_factory=uow_factory)
    tree = service.get_section_tree(document.id)

    assert len(tree) == 1
    assert tree[0].title == "Root"
    assert tree[0].children[0].title == "Child"


def test_get_section_content_uses_link_order(uow_factory):
    from app.repositories.document_repository import DocumentRepository
    from app.repositories.document_unit_repository import DocumentUnitRepository
    from app.repositories.section_repository import SectionRepository
    from app.repositories.section_unit_link_repository import SectionUnitLinkRepository
    from app.entities import SectionUnitLink

    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit_a = DocumentUnit(document_id=document.id, sequence_index=0, page_number=1, text_content="A")
    unit_b = DocumentUnit(document_id=document.id, sequence_index=1, page_number=2, text_content="B")
    section = Section(document_id=document.id, title="S1", level=1, order_index=0)

    with uow_factory() as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(unit_a)
        DocumentUnitRepository(uow.session).save(unit_b)
        SectionRepository(uow.session).save(section)
        SectionUnitLinkRepository(uow.session).save(
            SectionUnitLink(section_id=section.id, document_unit_id=unit_b.id, order_index=0)
        )
        SectionUnitLinkRepository(uow.session).save(
            SectionUnitLink(section_id=section.id, document_unit_id=unit_a.id, order_index=1)
        )
        uow.commit()

    service = SectionService(uow_factory=uow_factory)
    content = service.get_section_content(section.id)

    assert [unit.id for unit in content] == [unit_b.id, unit_a.id]


def test_get_section_content_raises_for_missing_section(uow_factory):
    service = SectionService(uow_factory=uow_factory)

    with pytest.raises(ValueError, match="Section not found"):
        service.get_section_content("missing")
```

- [ ] **Step 2: 运行 service 测试确认失败**

Run: `npm run test:python -- tests/unit/services/test_section_service.py -v`

Expected: FAIL，报 `SectionService` 缺失或方法未定义。

- [ ] **Step 3: 实现 repository 和 service 最小能力**

```python
class SectionRepository:
    def list_by_document(self, document_id: str) -> list[Section]:
        models = (
            self.session.query(SectionModel)
            .filter(SectionModel.document_id == document_id)
            .order_by(SectionModel.order_index, SectionModel.id)
            .all()
        )
        return [self._to_entity(model) for model in models]
```

```python
from sqlalchemy import case


class DocumentUnitRepository:
    def list_by_ids(self, unit_ids: list[str]) -> list[DocumentUnit]:
        if not unit_ids:
            return []
        models = (
            self.session.query(DocumentUnitModel)
            .filter(DocumentUnitModel.id.in_(unit_ids))
            .order_by(case({unit_id: index for index, unit_id in enumerate(unit_ids)}, value=DocumentUnitModel.id))
            .all()
        )
        return [self._to_entity(model) for model in models]
```

```python
from pydantic import BaseModel

from app.entities import Section, SectionUnitLink
from app.rag.page_index_builder import build_sections_from_units


class SectionTreeNode(BaseModel):
    id: str
    title: str
    level: int
    order_index: int
    children: list["SectionTreeNode"] = []


class SectionService:
    def __init__(self, uow_factory) -> None:
        self.uow_factory = uow_factory

    def build_sections(self, document_id: str) -> list[Section]:
        from app.repositories.document_unit_repository import DocumentUnitRepository
        from app.repositories.section_repository import SectionRepository
        from app.repositories.section_unit_link_repository import SectionUnitLinkRepository

        with self.uow_factory() as uow:
            section_repo = SectionRepository(uow.session)
            existing = section_repo.list_by_document(document_id)
            if existing:
                return existing

            units = DocumentUnitRepository(uow.session).list_by_document(document_id)
            sections = build_sections_from_units(document_id, units)
            link_repo = SectionUnitLinkRepository(uow.session)
            for section, unit in zip(sections, units, strict=False):
                section_repo.save(section)
                link_repo.save(
                    SectionUnitLink(section_id=section.id, document_unit_id=unit.id, order_index=0)
                )
            uow.commit()
            return sections

    def get_section_tree(self, document_id: str) -> list[SectionTreeNode]:
        from app.repositories.section_repository import SectionRepository

        with self.uow_factory() as uow:
            sections = SectionRepository(uow.session).list_by_document(document_id)

        nodes = {
            section.id: SectionTreeNode(
                id=section.id,
                title=section.title,
                level=section.level,
                order_index=section.order_index,
                children=[],
            )
            for section in sections
        }
        roots: list[SectionTreeNode] = []
        for section in sections:
            node = nodes[section.id]
            if section.parent_section_id and section.parent_section_id in nodes:
                nodes[section.parent_section_id].children.append(node)
            else:
                roots.append(node)
        return roots

    def get_section_content(self, section_id: str):
        from app.repositories.document_unit_repository import DocumentUnitRepository
        from app.repositories.section_repository import SectionRepository
        from app.repositories.section_unit_link_repository import SectionUnitLinkRepository

        with self.uow_factory() as uow:
            section_repo = SectionRepository(uow.session)
            section = section_repo.get_by_id(section_id)
            if section is None:
                raise ValueError(f"Section not found: {section_id}")

            link_repo = SectionUnitLinkRepository(uow.session)
            links = link_repo.list_by_section(section_id)
            if links:
                return DocumentUnitRepository(uow.session).list_by_ids(
                    [link.document_unit_id for link in links]
                )

            units = DocumentUnitRepository(uow.session).list_by_document(section.document_id)
            return [
                unit
                for unit in units
                if section.start_page is None
                or unit.page_number is None
                or section.start_page <= unit.page_number <= (section.end_page or section.start_page)
            ]
```

- [ ] **Step 4: 为 API 写失败测试**

```python
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import set_session_factory
from app.db.connection import create_app_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.entities import DocumentRecord, DocumentUnit
from app.enums import DocumentFileType
from app.main import app


def _fake_sqlite_vec_loader(connection):
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "data" / "section-api.sqlite3"
    session_factory = create_app_session_factory(
        database_path=database_path,
        embedding_dimension=8,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )
    set_session_factory(session_factory)

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        from app.repositories.document_repository import DocumentRepository
        from app.repositories.document_unit_repository import DocumentUnitRepository

        document = DocumentRecord(
            workspace_id="ws-1",
            title="Doc",
            original_filename="doc.pdf",
            file_type=DocumentFileType.PDF,
            file_path="data/uploads/doc.pdf",
        )
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(
            DocumentUnit(document_id=document.id, sequence_index=0, page_number=1, text_content="Page one")
        )
        uow.commit()

    yield TestClient(app), document.id
    set_session_factory(None)


def test_build_tree_and_content_roundtrip(client):
    test_client, document_id = client
    build_response = test_client.post(f"/api/sections/documents/{document_id}/build")
    assert build_response.status_code == 200
    section_id = build_response.json()["data"][0]["id"]

    tree_response = test_client.get(f"/api/sections/documents/{document_id}/tree")
    assert tree_response.status_code == 200
    assert tree_response.json()["data"][0]["title"] == "Page 1"

    content_response = test_client.get(f"/api/sections/{section_id}/content")
    assert content_response.status_code == 200
    assert content_response.json()["data"][0]["text_content"] == "Page one"


def test_get_section_content_returns_404_for_missing_section(client):
    test_client, _ = client
    response = test_client.get("/api/sections/missing/content")
    assert response.status_code == 404
```

- [ ] **Step 5: 运行 API 测试确认失败**

Run: `npm run test:python -- tests/integration/api/test_section_controller.py -v`

Expected: FAIL，报 section 路由未注册或 controller 缺失。

- [ ] **Step 6: 实现 schema、controller、依赖注册和 `main.py` 路由挂载**

```python
from datetime import datetime

from pydantic import BaseModel

from app.entities import DocumentUnit, Section
from app.services.section_service import SectionTreeNode


class SectionSummary(BaseModel):
    id: str
    document_id: str
    title: str
    level: int
    order_index: int
    start_page: int | None
    end_page: int | None

    @classmethod
    def from_entity(cls, section: Section) -> "SectionSummary":
        return cls(
            id=section.id,
            document_id=section.document_id,
            title=section.title,
            level=section.level,
            order_index=section.order_index,
            start_page=section.start_page,
            end_page=section.end_page,
        )


class SectionTreeNodeResponse(BaseModel):
    id: str
    title: str
    level: int
    order_index: int
    children: list["SectionTreeNodeResponse"]

    @classmethod
    def from_node(cls, node: SectionTreeNode) -> "SectionTreeNodeResponse":
        return cls(
            id=node.id,
            title=node.title,
            level=node.level,
            order_index=node.order_index,
            children=[cls.from_node(child) for child in node.children],
        )


class SectionContentUnit(BaseModel):
    id: str
    sequence_index: int
    page_number: int | None
    text_content: str

    @classmethod
    def from_entity(cls, unit: DocumentUnit) -> "SectionContentUnit":
        return cls(
            id=unit.id,
            sequence_index=unit.sequence_index,
            page_number=unit.page_number,
            text_content=unit.text_content,
        )
```

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_section_service
from app.schemas.section_schema import SectionContentUnit, SectionSummary, SectionTreeNodeResponse
from app.services.section_service import SectionService

router = APIRouter(prefix="/sections", tags=["Sections"])


@router.post("/documents/{document_id}/build")
def build_sections(document_id: str, service: Annotated[SectionService, Depends(get_section_service)]):
    sections = service.build_sections(document_id)
    return {"code": 200, "data": [SectionSummary.from_entity(section) for section in sections]}


@router.get("/documents/{document_id}/tree")
def get_section_tree(document_id: str, service: Annotated[SectionService, Depends(get_section_service)]):
    tree = service.get_section_tree(document_id)
    return {"code": 200, "data": [SectionTreeNodeResponse.from_node(node) for node in tree]}


@router.get("/{section_id}/content")
def get_section_content(section_id: str, service: Annotated[SectionService, Depends(get_section_service)]):
    try:
        units = service.get_section_content(section_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"code": 200, "data": [SectionContentUnit.from_entity(unit) for unit in units]}
```

```python
def get_section_service() -> SectionService:
    from app.services.section_service import SectionService

    return SectionService(uow_factory=_build_uow_factory())
```

```python
from app.api import document_controller, section_controller

app.include_router(document_controller.router, prefix="/api")
app.include_router(section_controller.router, prefix="/api")
```

- [ ] **Step 7: 运行测试确认通过**

Run: `npm run test:python -- tests/unit/services/test_section_service.py tests/integration/api/test_section_controller.py -v`

Expected: PASS。

### Task 4: 实现 ChunkService

**Files:**
- Modify: `backend-python/app/services/chunk_service.py`
- Modify: `backend-python/app/repositories/chunk_repository.py`
- Test: `backend-python/tests/unit/services/test_chunk_service.py`

- [ ] **Step 1: 写失败测试，覆盖切块窗口、空白跳过和文档持久化**

```python
import pytest

from app.db.connection import create_app_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.entities import DocumentRecord, DocumentUnit
from app.enums import DocumentFileType
from app.services.chunk_service import ChunkService


def _fake_sqlite_vec_loader(connection):
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def test_constructor_rejects_overlap_not_smaller_than_chunk_size():
    with pytest.raises(ValueError, match="overlap_chars"):
        ChunkService(uow_factory=lambda: None, max_chunk_size=100, overlap_chars=100)


def test_split_units_into_chunks_splits_long_text_and_skips_blank():
    service = ChunkService(uow_factory=lambda: None, max_chunk_size=5, overlap_chars=2)
    units = [
        DocumentUnit(document_id="doc-1", sequence_index=0, text_content="abcdefghij"),
        DocumentUnit(document_id="doc-1", sequence_index=1, text_content="   "),
    ]

    chunks = service.split_units_into_chunks(units)

    assert [chunk.text_content for chunk in chunks] == ["abcde", "defgh", "ghij"]
    assert [(chunk.start_char, chunk.end_char) for chunk in chunks] == [(0, 5), (3, 8), (6, 10)]
    assert all(chunk.document_unit_id == units[0].id for chunk in chunks)


def test_build_chunks_for_document_persists_chunks(tmp_path):
    database_path = tmp_path / "data" / "chunk.sqlite3"
    session_factory = create_app_session_factory(
        database_path=database_path,
        embedding_dimension=8,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )
    uow_factory = lambda: SqlAlchemyUnitOfWork(session_factory)

    from app.repositories.document_repository import DocumentRepository
    from app.repositories.document_unit_repository import DocumentUnitRepository
    from app.repositories.chunk_repository import ChunkRepository

    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit = DocumentUnit(document_id=document.id, sequence_index=0, text_content="abcdefgh")

    with uow_factory() as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(unit)
        uow.commit()

    service = ChunkService(uow_factory=uow_factory, max_chunk_size=4, overlap_chars=1)
    created = service.build_chunks_for_document(document.id)

    with uow_factory() as uow:
        persisted = ChunkRepository(uow.session).list_by_document(document.id)

    assert len(created) == 3
    assert [chunk.text_content for chunk in persisted] == ["abcd", "defg", "gh"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test:python -- tests/unit/services/test_chunk_service.py -v`

Expected: FAIL，报 `ChunkService` 未实现。

- [ ] **Step 3: 实现 repository 查询和 service 切分逻辑**

```python
from sqlalchemy import case
from sqlalchemy.orm import Session

from app.db.models import ChunkModel, DocumentUnitModel
from app.entities import Chunk


class ChunkRepository:
    def list_by_document(self, document_id: str) -> list[Chunk]:
        models = (
            self.session.query(ChunkModel)
            .join(DocumentUnitModel, DocumentUnitModel.id == ChunkModel.document_unit_id)
            .filter(DocumentUnitModel.document_id == document_id)
            .order_by(DocumentUnitModel.sequence_index, ChunkModel.sequence_index)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def list_by_ids(self, ids: list[str]) -> list[Chunk]:
        if not ids:
            return []
        models = (
            self.session.query(ChunkModel)
            .filter(ChunkModel.id.in_(ids))
            .order_by(case({chunk_id: index for index, chunk_id in enumerate(ids)}, value=ChunkModel.id))
            .all()
        )
        return [self._to_entity(model) for model in models]
```

```python
from app.entities import Chunk


class ChunkService:
    def __init__(self, uow_factory, *, max_chunk_size: int = 800, overlap_chars: int = 100) -> None:
        if overlap_chars >= max_chunk_size:
            raise ValueError("overlap_chars must be smaller than max_chunk_size")
        self.uow_factory = uow_factory
        self.max_chunk_size = max_chunk_size
        self.overlap_chars = overlap_chars

    def split_units_into_chunks(self, units):
        chunks: list[Chunk] = []
        step = self.max_chunk_size - self.overlap_chars
        for unit in units:
            text = unit.text_content.strip()
            if not text:
                continue
            original_text = unit.text_content
            for start in range(0, len(original_text), step):
                end = min(start + self.max_chunk_size, len(original_text))
                piece = original_text[start:end]
                if not piece.strip():
                    continue
                chunks.append(
                    Chunk(
                        document_unit_id=unit.id,
                        sequence_index=sum(1 for chunk in chunks if chunk.document_unit_id == unit.id),
                        text_content=piece,
                        start_char=start,
                        end_char=end,
                    )
                )
                if end == len(original_text):
                    break
        return chunks

    def build_chunks_for_document(self, document_id: str) -> list[Chunk]:
        from app.repositories.chunk_repository import ChunkRepository
        from app.repositories.document_unit_repository import DocumentUnitRepository

        with self.uow_factory() as uow:
            units = DocumentUnitRepository(uow.session).list_by_document(document_id)
            chunks = self.split_units_into_chunks(units)
            repo = ChunkRepository(uow.session)
            for chunk in chunks:
                repo.save(chunk)
            uow.commit()
            return chunks
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test:python -- tests/unit/services/test_chunk_service.py -v`

Expected: PASS。

### Task 5: 实现 Embedding Provider 和 EmbeddingService

**Files:**
- Modify: `backend-python/app/providers/base.py`
- Modify: `backend-python/app/providers/openai_compat_provider.py`
- Modify: `backend-python/app/services/embedding_service.py`
- Test: `backend-python/tests/unit/providers/test_openai_compat_provider.py`
- Test: `backend-python/tests/unit/services/test_embedding_service.py`

- [ ] **Step 1: 写 provider 失败测试，覆盖单文本和多文本 embedding**

```python
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.providers.base import EmbeddingResult
from app.providers.openai_compat_provider import OpenAICompatibleProvider


@patch("app.providers.openai_compat_provider.AsyncOpenAI")
@pytest.mark.asyncio
async def test_create_embedding_returns_single_embedding(MockAsyncOpenAI, provider_config_factory):
    mock_client = MockAsyncOpenAI.return_value
    mock_client.embeddings.create = AsyncMock(
        return_value=SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.1, 0.2])],
            model="embed-small",
        )
    )

    provider = OpenAICompatibleProvider(provider_config_factory())
    result = await provider.create_embedding("hello", model="embed-small")

    assert isinstance(result, EmbeddingResult)
    assert result.embeddings == [[0.1, 0.2]]
    assert result.model == "embed-small"


@patch("app.providers.openai_compat_provider.AsyncOpenAI")
@pytest.mark.asyncio
async def test_create_embedding_passes_text_list(MockAsyncOpenAI, provider_config_factory):
    mock_client = MockAsyncOpenAI.return_value
    mock_client.embeddings.create = AsyncMock(
        return_value=SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.1, 0.2]), SimpleNamespace(embedding=[0.3, 0.4])],
            model="embed-small",
        )
    )

    provider = OpenAICompatibleProvider(provider_config_factory())
    await provider.create_embedding(["hello", "world"], model="embed-small")

    kwargs = mock_client.embeddings.create.call_args[1]
    assert kwargs["input"] == ["hello", "world"]
    assert kwargs["model"] == "embed-small"
```

- [ ] **Step 2: 运行 provider 测试确认失败**

Run: `npm run test:python -- tests/unit/providers/test_openai_compat_provider.py -v`

Expected: FAIL，报 `EmbeddingResult` 或 `create_embedding` 缺失。

- [ ] **Step 3: 写 service 失败测试，覆盖成功写入和数量不匹配回滚**

```python
from types import SimpleNamespace

import pytest

from app.db.connection import create_app_session_factory
from app.db.unit_of_work import SqlAlchemyUnitOfWork
from app.entities import Chunk, DocumentRecord, DocumentUnit
from app.enums import DocumentFileType
from app.providers.base import EmbeddingResult
from app.services.embedding_service import EmbeddingService


def _fake_sqlite_vec_loader(connection):
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


class FakeProvider:
    def __init__(self, result: EmbeddingResult) -> None:
        self.result = result

    async def create_embedding(self, input, model=None):
        return self.result


@pytest.fixture
def session_factory(tmp_path):
    database_path = tmp_path / "data" / "embedding.sqlite3"
    return create_app_session_factory(
        database_path=database_path,
        embedding_dimension=2,
        sqlite_vec_loader=_fake_sqlite_vec_loader,
    )


def _seed_chunks(session_factory):
    from app.repositories.chunk_repository import ChunkRepository
    from app.repositories.document_repository import DocumentRepository
    from app.repositories.document_unit_repository import DocumentUnitRepository

    document = DocumentRecord(
        workspace_id="ws-1",
        title="Doc",
        original_filename="doc.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/doc.pdf",
    )
    unit = DocumentUnit(document_id=document.id, sequence_index=0, text_content="Source")
    chunks = [
        Chunk(document_unit_id=unit.id, sequence_index=0, text_content="chunk-a"),
        Chunk(document_unit_id=unit.id, sequence_index=1, text_content="chunk-b"),
    ]

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        DocumentRepository(uow.session).save(document)
        DocumentUnitRepository(uow.session).save(unit)
        for chunk in chunks:
            ChunkRepository(uow.session).save(chunk)
        uow.commit()
    return chunks


@pytest.mark.asyncio
async def test_embed_chunks_saves_all_vectors(session_factory):
    chunks = _seed_chunks(session_factory)
    service = EmbeddingService(
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        provider=FakeProvider(EmbeddingResult(embeddings=[[0.1, 0.2], [0.3, 0.4]], model="embed-small")),
        embedding_dimension=2,
    )

    saved = await service.embed_chunks(chunks, model="embed-small")

    assert len(saved) == 2


@pytest.mark.asyncio
async def test_embed_chunks_rolls_back_when_embedding_count_mismatches(session_factory):
    chunks = _seed_chunks(session_factory)
    service = EmbeddingService(
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        provider=FakeProvider(EmbeddingResult(embeddings=[[0.1, 0.2]], model="embed-small")),
        embedding_dimension=2,
    )

    with pytest.raises(ValueError, match="Embedding count mismatch"):
        await service.embed_chunks(chunks, model="embed-small")

    from app.repositories.embedding_repository import EmbeddingRepository
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert EmbeddingRepository(uow.session, embedding_dimension=2).get_by_chunk_id(chunks[0].id) is None
```

- [ ] **Step 4: 运行 service 测试确认失败**

Run: `npm run test:python -- tests/unit/services/test_embedding_service.py -v`

Expected: FAIL，报 `EmbeddingService` 未实现。

- [ ] **Step 5: 实现 provider 抽象和 service 原子写入**

```python
from abc import ABC, abstractmethod


class ChatResult:
    def __init__(self, content: str) -> None:
        self.content = content


class EmbeddingResult:
    def __init__(self, embeddings: list[list[float]], model: str) -> None:
        self.embeddings = embeddings
        self.model = model


class AIProvider(ABC):
    @abstractmethod
    async def chat_completion(self, messages: list[dict], model: str | None = None, temperature: float = 0.3, max_tokens: int | None = None, response_format: dict | None = None) -> ChatResult:
        ...

    @abstractmethod
    async def create_embedding(self, input: str | list[str], model: str | None = None) -> EmbeddingResult:
        ...
```

```python
async def create_embedding(self, input: str | list[str], model: str | None = None) -> EmbeddingResult:
    if model is None:
        raise ValueError("Embedding model is required")
    response = await self._client.embeddings.create(model=model, input=input)
    return EmbeddingResult(
        embeddings=[item.embedding for item in response.data],
        model=response.model,
    )
```

```python
from app.repositories.embedding_repository import ChunkEmbedding, EmbeddingRepository


class EmbeddingService:
    def __init__(self, uow_factory, provider, *, embedding_dimension: int) -> None:
        self.uow_factory = uow_factory
        self.provider = provider
        self.embedding_dimension = embedding_dimension

    async def embed_chunks(self, chunks, *, model: str):
        if model is None:
            raise ValueError("Embedding model is required")
        texts = [chunk.text_content for chunk in chunks]
        result = await self.provider.create_embedding(texts, model=model)
        if len(result.embeddings) != len(chunks):
            raise ValueError(
                f"Embedding count mismatch: expected {len(chunks)}, got {len(result.embeddings)}"
            )

        with self.uow_factory() as uow:
            repo = EmbeddingRepository(uow.session, embedding_dimension=self.embedding_dimension)
            saved = []
            for chunk, vector in zip(chunks, result.embeddings, strict=True):
                saved.append(
                    repo.save_for_chunk(
                        chunk_id=chunk.id,
                        embedding_model=result.model,
                        vector=vector,
                    )
                )
            uow.commit()
            return saved
```

- [ ] **Step 6: 运行测试确认通过**

Run: `npm run test:python -- tests/unit/providers/test_openai_compat_provider.py tests/unit/services/test_embedding_service.py -v`

Expected: PASS。

### Task 6: 实现 Retriever

**Files:**
- Modify: `backend-python/app/repositories/embedding_repository.py`
- Modify: `backend-python/app/rag/retriever.py`
- Test: `backend-python/tests/unit/rag/test_retriever.py`

- [ ] **Step 1: 写失败测试，覆盖排序、空索引和维度不一致跳过**

```python
from datetime import datetime, timezone

from app.entities import Chunk
from app.rag.retriever import Retriever
from app.repositories.embedding_repository import ChunkEmbedding


class FakeEmbeddingRepository:
    def __init__(self, embeddings):
        self.embeddings = embeddings

    def list_by_document(self, document_id: str):
        return self.embeddings


class FakeChunkRepository:
    def __init__(self, chunks):
        self.chunks = chunks

    def list_by_ids(self, ids: list[str]):
        by_id = {chunk.id: chunk for chunk in self.chunks}
        return [by_id[chunk_id] for chunk_id in ids if chunk_id in by_id]


def test_retrieve_returns_top_k_sorted_by_score():
    embeddings = [
        ChunkEmbedding(id="e1", chunk_id="c1", embedding_model="m", vector_dimension=2, vector=[1.0, 0.0], created_at=datetime.now(timezone.utc)),
        ChunkEmbedding(id="e2", chunk_id="c2", embedding_model="m", vector_dimension=2, vector=[0.0, 1.0], created_at=datetime.now(timezone.utc)),
    ]
    chunks = [
        Chunk(id="c1", document_unit_id="u1", sequence_index=0, text_content="alpha"),
        Chunk(id="c2", document_unit_id="u1", sequence_index=1, text_content="beta"),
    ]
    retriever = Retriever(FakeEmbeddingRepository(embeddings), FakeChunkRepository(chunks))

    results = retriever.retrieve(document_id="doc-1", query_embedding=[1.0, 0.0], top_k=1)

    assert len(results) == 1
    assert results[0].chunk_id == "c1"
    assert results[0].text_content == "alpha"


def test_retrieve_returns_empty_when_index_is_empty():
    retriever = Retriever(FakeEmbeddingRepository([]), FakeChunkRepository([]))
    assert retriever.retrieve(document_id="doc-1", query_embedding=[1.0, 0.0], top_k=3) == []


def test_retrieve_skips_vectors_with_wrong_dimension():
    embeddings = [
        ChunkEmbedding(id="e1", chunk_id="c1", embedding_model="m", vector_dimension=3, vector=[1.0, 0.0, 0.0], created_at=datetime.now(timezone.utc)),
        ChunkEmbedding(id="e2", chunk_id="c2", embedding_model="m", vector_dimension=2, vector=[0.5, 0.5], created_at=datetime.now(timezone.utc)),
    ]
    chunks = [
        Chunk(id="c1", document_unit_id="u1", sequence_index=0, text_content="alpha"),
        Chunk(id="c2", document_unit_id="u1", sequence_index=1, text_content="beta"),
    ]
    retriever = Retriever(FakeEmbeddingRepository(embeddings), FakeChunkRepository(chunks))

    results = retriever.retrieve(document_id="doc-1", query_embedding=[1.0, 0.0], top_k=2)

    assert [result.chunk_id for result in results] == ["c2"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test:python -- tests/unit/rag/test_retriever.py -v`

Expected: FAIL，报 `Retriever` 未实现。

- [ ] **Step 3: 实现查询和余弦相似度检索**

```python
from sqlalchemy.orm import Session

from app.db.models import ChunkModel, DocumentUnitModel, EmbeddingVectorModel
from app.repositories.sqlite_helpers import json_array


class EmbeddingRepository:
    def list_by_document(self, document_id: str) -> list[ChunkEmbedding]:
        rows = (
            self.session.query(EmbeddingVectorModel)
            .join(ChunkModel, ChunkModel.id == EmbeddingVectorModel.chunk_id)
            .join(DocumentUnitModel, DocumentUnitModel.id == ChunkModel.document_unit_id)
            .filter(DocumentUnitModel.document_id == document_id)
            .order_by(ChunkModel.sequence_index)
            .all()
        )
        return [
            ChunkEmbedding(
                id=row.id,
                chunk_id=row.chunk_id,
                embedding_model=row.embedding_model,
                vector_dimension=row.vector_dimension,
                vector=json_array(row.vector_json),
                created_at=row.created_at,
            )
            for row in rows
        ]
```

```python
from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: str
    text_content: str
    score: float


class Retriever:
    def __init__(self, embedding_repository, chunk_repository) -> None:
        self.embedding_repository = embedding_repository
        self.chunk_repository = chunk_repository

    def retrieve(self, *, document_id: str, query_embedding: list[float], top_k: int = 5) -> list[RetrievalResult]:
        embeddings = self.embedding_repository.list_by_document(document_id)
        if not embeddings:
            return []

        scored: list[tuple[str, float]] = []
        for embedding in embeddings:
            if len(embedding.vector) != len(query_embedding):
                continue
            score = self._cosine_similarity(query_embedding, embedding.vector)
            scored.append((embedding.chunk_id, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        chunk_ids = [chunk_id for chunk_id, _score in scored[:top_k]]
        chunks = self.chunk_repository.list_by_ids(chunk_ids)
        score_by_id = {chunk_id: score for chunk_id, score in scored[:top_k]}
        return [
            RetrievalResult(chunk_id=chunk.id, text_content=chunk.text_content, score=score_by_id[chunk.id])
            for chunk in chunks
            if chunk.id in score_by_id
        ]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = sqrt(sum(value * value for value in left))
        right_norm = sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test:python -- tests/unit/rag/test_retriever.py -v`

Expected: PASS。

### Task 7: 聚合验证

**Files:**
- Verify only

- [ ] **Step 1: 运行本次后端主链路测试集合**

Run: `npm run test:python -- tests/unit/rag tests/unit/services/test_section_service.py tests/unit/services/test_chunk_service.py tests/unit/services/test_embedding_service.py tests/unit/providers/test_openai_compat_provider.py tests/integration/persistence/test_section_unit_link_repository.py tests/integration/api/test_section_controller.py -v`

Expected: PASS，所有新增主链路测试通过。

- [ ] **Step 2: 运行关联回归测试**

Run: `npm run test:python -- tests/integration/persistence/test_database_initialization.py tests/integration/persistence/test_sqlalchemy_persistence.py tests/unit/db/test_connection.py -v`

Expected: PASS，确认 schema 变更未破坏数据库初始化与持久化基础能力。

- [ ] **Step 3: 检查工作区变更范围**

Run: `git status --short`

Expected: 只出现本次 `pageindex/rag/section/chunk/provider` 相关文件与既有未处理改动。

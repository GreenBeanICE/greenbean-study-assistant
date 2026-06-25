# RAG Pipeline Auto Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让文档上传后自动串联解析、切块、章节构建和向量化，在 embedding 失败时仍保留前置成果。

**Architecture:** 保持现有 `DocumentIngestService` 作为上传入口编排点，不引入新的 orchestrator。同步 `ingest_document` 继续负责解析、持久化、切块、章节构建；新增 `ingest_document_async` 包装异步 embedding，并由 `document_controller` 在上传接口中调用。依赖注入层负责把 `ChunkService`、`SectionService`、`EmbeddingService` 装配进来。

**Tech Stack:** Python 3.12、FastAPI、pytest、Pydantic v2、SQLAlchemy UOW、async/await。

---

### Task 1: 为自动串联流水线补失败测试

**Files:**
- Modify: `backend-python/tests/unit/services/test_document_ingest_service.py`
- Test: `backend-python/tests/unit/services/test_document_ingest_service.py`

- [ ] **Step 1: Write the failing sync pipeline test**

在 `backend-python/tests/unit/services/test_document_ingest_service.py` 末尾新增一个同步测试，验证 `ingest_document` 在注入 `chunk_service` 和 `section_service` 后会把结果挂回返回值。

```python
@pytest.mark.us25
def test_ingest_document_runs_chunk_and_section_pipeline():
    chunk_service = MagicMock()
    chunk_service.build_chunks_for_document.return_value = ["chunk-a"]
    section_service = MagicMock()
    section_service.build_sections.return_value = ["section-a"]
    service = DocumentIngestService(
        chunk_service=chunk_service,
        section_service=section_service,
    )

    with patch("app.parsers.parser_factory.ParserFactory.get_parser") as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [_make_page(content="hello", source_type="text")]
        mock_get_parser.return_value = mock_parser

        result = service.ingest_document("notes.txt", b"content")

    chunk_service.build_chunks_for_document.assert_called_once_with(
        result["document_record"].id
    )
    section_service.build_sections.assert_called_once_with(result["document_record"].id)
    assert result["chunks"] == ["chunk-a"]
    assert result["sections"] == ["section-a"]
    assert result["embeddings"] == []
```

- [ ] **Step 2: Write the failing async embedding success test**

继续在同一文件新增异步测试，验证 `ingest_document_async` 会 await embedding 并把结果写回返回值。

```python
@pytest.mark.us25
@pytest.mark.asyncio
async def test_ingest_document_async_runs_embedding_after_chunk_pipeline():
    chunk_service = MagicMock()
    chunk_service.build_chunks_for_document.return_value = [MagicMock(text_content="chunk text")]
    section_service = MagicMock()
    section_service.build_sections.return_value = ["section-a"]
    embedding_service = MagicMock()
    embedding_service.embed_chunks = AsyncMock(return_value=["embedding-a"])
    service = DocumentIngestService(
        chunk_service=chunk_service,
        section_service=section_service,
        embedding_service=embedding_service,
    )

    with patch("app.parsers.parser_factory.ParserFactory.get_parser") as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [_make_page(content="hello", source_type="text")]
        mock_get_parser.return_value = mock_parser

        result = await service.ingest_document_async(
            filename="notes.txt",
            file_content=b"content",
        )

    embedding_service.embed_chunks.assert_awaited_once_with([chunk_service.build_chunks_for_document.return_value[0]])
    assert result["embeddings"] == ["embedding-a"]
```

- [ ] **Step 3: Write the failing async graceful-degrade test**

再补一条 embedding 抛异常时仍然成功返回的测试。

```python
@pytest.mark.us25
@pytest.mark.asyncio
async def test_ingest_document_async_keeps_upload_success_when_embedding_fails():
    chunk = MagicMock(text_content="chunk text")
    chunk_service = MagicMock()
    chunk_service.build_chunks_for_document.return_value = [chunk]
    section_service = MagicMock()
    section_service.build_sections.return_value = ["section-a"]
    embedding_service = MagicMock()
    embedding_service.embed_chunks = AsyncMock(side_effect=RuntimeError("embed failed"))
    service = DocumentIngestService(
        chunk_service=chunk_service,
        section_service=section_service,
        embedding_service=embedding_service,
    )

    with patch("app.parsers.parser_factory.ParserFactory.get_parser") as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [_make_page(content="hello", source_type="text")]
        mock_get_parser.return_value = mock_parser

        result = await service.ingest_document_async(
            filename="notes.txt",
            file_content=b"content",
        )

    assert result["chunks"] == [chunk]
    assert result["sections"] == ["section-a"]
    assert result["embeddings"] == []
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `rtk pytest backend-python/tests/unit/services/test_document_ingest_service.py -q`

Expected: 新增用例失败，典型失败包括 `TypeError: __init__ got an unexpected keyword argument 'chunk_service'` 或 `AttributeError: 'DocumentIngestService' object has no attribute 'ingest_document_async'`。

- [ ] **Step 5: Commit**

```bash
git add backend-python/tests/unit/services/test_document_ingest_service.py
git commit -m "test(python): cover ingest rag pipeline wiring"
```

### Task 2: 最小实现 DocumentIngestService 串联逻辑

**Files:**
- Modify: `backend-python/app/services/document_ingest_service.py`
- Test: `backend-python/tests/unit/services/test_document_ingest_service.py`

- [ ] **Step 1: Extend constructor dependencies**

把 `DocumentIngestService.__init__` 扩成下面这样，保持默认值为 `None`，不破坏现有单元测试和内存模式。

```python
class DocumentIngestService:
    def __init__(
        self,
        uow_factory=None,
        *,
        chunk_service=None,
        embedding_service=None,
        section_service=None,
    ):
        self.uow_factory = uow_factory
        self.chunk_service = chunk_service
        self.embedding_service = embedding_service
        self.section_service = section_service
```

- [ ] **Step 2: Add sync post-ingest pipeline**

在 `ingest_document` 的返回前追加同步后处理，只做切块和章节构建，不做 embedding。

```python
        chunks = []
        if self.chunk_service is not None:
            chunks = self.chunk_service.build_chunks_for_document(document_record.id)

        sections = []
        if self.section_service is not None:
            sections = self.section_service.build_sections(document_record.id)

        return {
            "filename": filename,
            "total_pages": len(parsed_pages),
            "status": "parsed_successfully",
            "page_index_preview": page_index_preview,
            "document_record": document_record,
            "document_units": document_units,
            "chunks": chunks,
            "sections": sections,
            "embeddings": [],
        }
```

- [ ] **Step 3: Add async wrapper for embedding**

在同一个类里新增异步包装方法，复用同步结果并只在有 chunk 时尝试 embedding。

```python
    async def ingest_document_async(
        self,
        filename: str,
        file_content: bytes,
        *,
        workspace_id: str = "",
        title: str | None = None,
        file_path: str = "",
        file_hash: str | None = None,
    ) -> dict:
        result = self.ingest_document(
            filename,
            file_content,
            workspace_id=workspace_id,
            title=title,
            file_path=file_path,
            file_hash=file_hash,
        )

        chunks = result["chunks"]
        if self.embedding_service is None or not chunks:
            return result

        try:
            result["embeddings"] = await self.embedding_service.embed_chunks(chunks)
        except Exception:
            result["embeddings"] = []
        return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `rtk pytest backend-python/tests/unit/services/test_document_ingest_service.py -q`

Expected: PASS，新增流水线测试和原有摄取测试全部通过。

- [ ] **Step 5: Commit**

```bash
git add backend-python/app/services/document_ingest_service.py backend-python/tests/unit/services/test_document_ingest_service.py
git commit -m "feat(python): auto wire ingest pipeline stages"
```

### Task 3: 装配依赖并切换上传入口到异步流水线

**Files:**
- Modify: `backend-python/app/api/dependencies.py`
- Modify: `backend-python/app/api/document_controller.py`
- Modify: `backend-python/tests/unit/api/test_dependencies.py`
- Modify: `backend-python/tests/integration/api/test_document_controller.py`

- [ ] **Step 1: Write the failing dependency and controller tests**

先在 `backend-python/tests/unit/api/test_dependencies.py` 增加 `get_chunk_service` 的未装配失败测试：

```python
from app.api.dependencies import get_chunk_service


@pytest.mark.unit
def test_get_chunk_service_raises_when_not_configured():
    set_session_factory(None)
    with pytest.raises(RuntimeError, match="Session factory is not configured"):
        get_chunk_service()
```

再把 `backend-python/tests/integration/api/test_document_controller.py` 中所有 `self.mock_service.ingest_document` 改为 `self.mock_service.ingest_document_async = AsyncMock(...)`，例如：

```python
    def test_upload_pdf_success(self):
        self.mock_service.ingest_document_async = AsyncMock(
            return_value=_make_ingest_result("test.pdf", "pdf")
        )
        response = self.client.post(
            "/api/documents/upload", files=_create_test_file(b"%PDF-1.4", "test.pdf")
        )
```

对应的异常场景也要改成：

```python
        self.mock_service.ingest_document_async = AsyncMock(side_effect=ValueError("业务异常"))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `rtk pytest backend-python/tests/unit/api/test_dependencies.py backend-python/tests/integration/api/test_document_controller.py -q`

Expected: FAIL，至少会出现 `ImportError`/`AttributeError`（尚无 `get_chunk_service`）或 controller 仍在调用 `ingest_document` 导致 AsyncMock 未生效。

- [ ] **Step 3: Write minimal dependency wiring**

在 `backend-python/app/api/dependencies.py` 增加 `ChunkService` 导入和工厂函数，并更新 `get_ingest_service`：

```python
from app.services.chunk_service import ChunkService


def get_chunk_service() -> ChunkService:
    return ChunkService(uow_factory=_build_uow_factory())


def get_ingest_service() -> DocumentIngestService:
    return DocumentIngestService(
        uow_factory=_build_uow_factory(),
        chunk_service=get_chunk_service(),
        embedding_service=get_embedding_service(),
        section_service=get_section_service(),
    )
```

- [ ] **Step 4: Switch upload controller to async ingest**

把 `backend-python/app/api/document_controller.py` 中这段：

```python
        result = ingest_service.ingest_document(
            file.filename,
            file_content,
            workspace_id=workspace_id,
            file_hash=file_hash,
        )
```

改成：

```python
        result = await ingest_service.ingest_document_async(
            file.filename,
            file_content,
            workspace_id=workspace_id,
            file_hash=file_hash,
        )
```

并把直接调用 `upload_document(...)` 的单测里 mock service 也补成：

```python
            mock_service = MagicMock()
            mock_service.ingest_document_async = AsyncMock(return_value=_make_ingest_result())
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `rtk pytest backend-python/tests/unit/api/test_dependencies.py backend-python/tests/integration/api/test_document_controller.py -q`

Expected: PASS，说明依赖装配与上传入口都切到了新流水线。

- [ ] **Step 6: Commit**

```bash
git add backend-python/app/api/dependencies.py backend-python/app/api/document_controller.py backend-python/tests/unit/api/test_dependencies.py backend-python/tests/integration/api/test_document_controller.py
git commit -m "feat(api): wire upload endpoint to async ingest pipeline"
```

### Task 4: 做最小范围回归验证

**Files:**
- Modify: `backend-python/app/services/document_ingest_service.py`
- Modify: `backend-python/app/api/dependencies.py`
- Modify: `backend-python/app/api/document_controller.py`
- Modify: `backend-python/tests/unit/services/test_document_ingest_service.py`
- Modify: `backend-python/tests/unit/api/test_dependencies.py`
- Modify: `backend-python/tests/integration/api/test_document_controller.py`

- [ ] **Step 1: Run the nearest combined Python test scope**

Run: `rtk pytest backend-python/tests/unit/services/test_document_ingest_service.py backend-python/tests/unit/api/test_dependencies.py backend-python/tests/integration/api/test_document_controller.py -q`

Expected: PASS，证明服务、依赖和上传接口三段链路一起工作。

- [ ] **Step 2: Run a slightly broader ingestion-related scope**

Run: `rtk pytest backend-python/tests/unit/services/test_chunk_service.py backend-python/tests/unit/services/test_embedding_service.py backend-python/tests/unit/services/test_section_service.py backend-python/tests/integration/api/test_document_controller.py -q`

Expected: PASS，确认这次串联没有破坏 chunk、embedding、section 的既有行为。

- [ ] **Step 3: Inspect final diff briefly**

Run: `git diff --stat`

Expected: 主要集中在以下 6 个文件：

```text
backend-python/app/services/document_ingest_service.py
backend-python/app/api/dependencies.py
backend-python/app/api/document_controller.py
backend-python/tests/unit/services/test_document_ingest_service.py
backend-python/tests/unit/api/test_dependencies.py
backend-python/tests/integration/api/test_document_controller.py
```

如果 diff 中出现无关文件，不要回滚它们，只在交付说明里声明工作区本来就有其他改动。

- [ ] **Step 4: Prepare handoff notes**

交付说明至少覆盖：

```text
1. 上传后现在会自动完成切块、章节构建和 embedding。
2. embedding 失败不会让上传失败，前置解析结果仍保留。
3. 目前只串流水线，不包含 vector_index_builder/context_builder/reranker 的补齐。
```

- [ ] **Step 5: Commit**

```bash
git add backend-python/app/services/document_ingest_service.py backend-python/app/api/dependencies.py backend-python/app/api/document_controller.py backend-python/tests/unit/services/test_document_ingest_service.py backend-python/tests/unit/api/test_dependencies.py backend-python/tests/integration/api/test_document_controller.py
git commit -m "test(python): verify automatic rag pipeline wiring"
```

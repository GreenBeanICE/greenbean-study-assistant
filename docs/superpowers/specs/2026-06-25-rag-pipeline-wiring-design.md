# 上传文档后自动串联 RAG 流水线 设计文档

## 目标

上传文档后自动跑完：解析 → 切块 → 章节构建 → 向量化，全程无需手动操作。Embedding 失败时不回滚，解析+切块+章节照常持久化，后续可补。

## 当前状态

- `DocumentIngestService.ingest_document()` 完成解析→DocumentRecord→DocumentUnit→持久化后就返回了
- `ChunkService`、`EmbeddingService`、`SectionService` 各自独立有真实逻辑
- `dependencies.py` 有 `get_embedding_service` 和 `get_section_service`，但没有 `get_chunk_service`
- `embed_chunks` 是 async，`ingest_document` 是 sync；需要新增 `ingest_document_async` 包装方法

## 设计方案

### 核心改动：扩展 DocumentIngestService

在 `DocumentIngestService.__init__` 中增加三个可选依赖（默认 None 保持向后兼容）：

```python
def __init__(self, uow_factory=None, *, chunk_service=None, embedding_service=None, section_service=None):
    self.uow_factory = uow_factory
    self.chunk_service = chunk_service
    self.embedding_service = embedding_service
    self.section_service = section_service
```

在 `ingest_document` 的持久化步骤之后，追加同步流水线（切块、章节）：

```python
# ---- Step 5: 切块 ----
chunks = []
if self.chunk_service is not None:
    chunks = self.chunk_service.build_chunks_for_document(document_record.id)

# ---- Step 6: 章节构建 ----
sections = []
if self.section_service is not None:
    sections = self.section_service.build_sections(document_record.id)
```

新增 `async def ingest_document_async` 包装同步流程并追加异步向量化：

```python
async def ingest_document_async(self, **kwargs) -> dict:
    result = self.ingest_document(**kwargs)
    chunks = result.get("chunks", [])
    embeddings = []
    if self.embedding_service is not None and chunks:
        try:
            embeddings = await self.embedding_service.embed_chunks(chunks)
        except Exception:
            pass  # embedding 失败不影响上传结果
    result["embeddings"] = embeddings
    return result
```

`document_controller.py` 的 `upload_document` 改为调用 `ingest_document_async`：

```python
result = await ingest_service.ingest_document_async(...)
```

返回结果扩展：

```python
return {
    ...,
    "chunks": chunks,
    "sections": sections,
    "embeddings": embeddings,
}
```

### 依赖注入改动

`dependencies.py` 新增 `get_chunk_service`：

```python
def get_chunk_service() -> ChunkService:
    return ChunkService(uow_factory=_build_uow_factory())
```

更新 `get_ingest_service` 传入下游服务：

```python
def get_ingest_service() -> DocumentIngestService:
    return DocumentIngestService(
        uow_factory=_build_uow_factory(),
        chunk_service=get_chunk_service(),
        section_service=get_section_service(),
        embedding_service=get_embedding_service(),
    )
```

### 文件变更清单

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `backend-python/app/services/document_ingest_service.py` | 修改 | 构造函数加3个可选依赖，ingest_document 末尾追加切块→章节，新增 ingest_document_async 包装异步向量化 |
| `backend-python/app/api/dependencies.py` | 修改 | 新增 get_chunk_service，更新 get_ingest_service 传入下游 |
| `backend-python/app/api/document_controller.py` | 修改 | upload_document 改调 ingest_document_async |
| `backend-python/tests/unit/services/test_document_ingest_service.py` | 新增 | 测试流水线串联逻辑 |

### 不改的部分

- `vector_index_builder.py`、`context_builder.py`、`reranker.py` 保持占位
- 前端上传 UI 不在本次范围

### 测试策略

1. 有全部服务时：调用 `ingest_document_async`，验证 chunks、sections、embeddings 都生成
2. 无 embedding_service 时：验证 chunks 和 sections 正常，embeddings 为空
3. embedding 抛异常时：验证上传仍然成功，embeddings 为空
4. 无 chunk_service 时：验证只做解析和持久化（向后兼容，ingest_document 不受影响）
5. 纯 sync 调用（ingest_document）：验证只有 chunks 和 sections，无 embeddings

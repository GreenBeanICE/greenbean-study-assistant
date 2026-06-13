# GreenBean Parser ↔ Database 集成技术规格

> **文档版本**：v1.0  
> **发布日期**：2026-05-18  
> **状态**：Draft → Review  
> **适用范围**：Parser 团队（US #25 负责人）+ Database 团队  
> **对应 User Story**：[#25 — 课程文档上传与 PageIndex 结构化解析](https://github.com/GreenBeanICE/greenbean-study-assistant/issues/25)

---

## 目录

1. [概述与范围](#1-概述与范围)
2. [当前状态评估](#2-当前状态评估)
3. [PageIndex 数据契约](#3-pageindex-数据契约解析器标准化输出)
4. [实体填充映射规格](#4-实体填充映射规格-pageindex--数据库实体)
5. [数据库缺失清单](#5-数据库缺失清单)
6. [Repository 接口契约](#6-repository-接口契约)
7. [安全摄入流水线设计](#7-安全摄入流水线设计)
8. [状态机与生命周期](#8-状态机与生命周期)
9. [安全设计矩阵](#9-安全设计矩阵)
10. [团队职责与交付边界](#10-团队职责与交付边界)
11. [实施路线图](#11-实施路线图)
12. [测试要求](#12-测试要求)
13. [附录](#13-附录)

---

## 1. 概述与范围

### 1.1 文档目的

本文档定义 Parser 层（US #25 产出物）与 Database 层（RAG 持久化设施）之间的**完整接口契约**和**集成方案**。它是一份双方团队共同遵守的技术规格：

- **Parser 团队**：据此补足 Parser 输出格式的标准化、补齐缺失字段、实施安全摄入流水线。
- **Database 团队**：据此补齐缺失的表/模型/仓库、实现批量操作接口、建立向量索引基础设施。

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **低耦合** | Parser 与 DB 的唯一耦合点是 `app/entities/` 下的 Pydantic 实体定义；Parser 通过 Repository 接口调用 DB，不关心底层 SQL/ORM 实现 |
| **契约优先** | 先定义接口签名和数据格式，双方各自实现，通过集成测试验证 |
| **事务安全** | 所有写入操作包裹在 `SqlAlchemyUnitOfWork` 中，保证原子性 |
| **幂等性** | 所有 Repository.save() 采用 upsert 模式（get-or-create + update） |
| **可追溯性** | 每个实体记录 parser_name、parser_version、时间戳，支持审计回溯 |
| **渐进式交付** | 解析→实体化→章节化→切块→向量化，分阶段交付，每阶段可独立验证 |

### 1.3 术语

| 术语 | 定义 |
|------|------|
| **PageIndex 节点** | 单个解析器的输出单元，代表 PDF 的一页、PPT 的一张 slide、Word/Text/Image 的整体文本。格式为 `{page_number, content, char_count, parser_name, parser_version, metadata}` |
| **DocumentUnit** | PageIndex 节点持久化到数据库后的实体，是 RAG 检索的最小原文单元 |
| **Chunk** | 对 DocumentUnit 的文本进行切分后的语义片段，用于向量化 |
| **EmbeddingVector** | Chunk 经 embedding 模型计算后的向量表示 |
| **Section** | 文档的层级章节结构，通过 headings 提取构建 |
| **SectionUnitLink** | Section 与 DocumentUnit 的多对多关联记录 |

---

## 2. 当前状态评估

### 2.1 Parser 层状态（US #25）

| 模块 | 状态 | 质量 |
|------|------|------|
| `ParserFactory` | ✅ 完成 | 路由逻辑全覆盖，大小写不敏感，12 个测试全绿 |
| `PDFParser` | ✅ 完成 | mock 隔离测试通过，逐页提取 page_number/content/char_count |
| `WordParser` | ✅ 完成 | 段落+表格+标题提取，空段落跳过，5 个测试全绿 |
| `PptParser` | ✅ 完成 | 逐 slide，标题检测(idx==0)，空 PPT 处理，6 个测试全绿 |
| `TextParser` | ✅ 完成 | UTF-8→GBK→Latin-1 回退，Markdown 检测，7 个测试全绿 |
| `ImageOCRParser` | ✅ 完成 | Tesseract 中英法，OCR 失败降级，8 个测试全绿 |
| `ImagePreprocessor` | ✅ 完成 | 缩放→灰度→降噪→对比度→二值化，15 个测试全绿 |
| `DocumentIngestService` | ⚠️ 部分 | 仅返回内存 preview，未持久化到 DB |
| `DocumentController` | ✅ 完成 | POST /api/documents/upload，完整错误处理，13 个测试全绿 |
| `file_utils` | ✅ 完成 | 扩展名检测/MIME 映射，但 `.doc` 在支持列表内却无对应 Parser |
| `text_utils` | ✅ 完成 | 清洗/截断/分词/语言检测，所有函数已测试 |

**测试汇总**：US #25 相关的 11 个测试文件，**122 个测试用例，0 失败**。

### 2.2 Database 层状态

| 组件 | 状态 | 备注 |
|------|------|------|
| `document_records` 表 + ORM + Repo | ✅ 完成 | upsert + get_by_id |
| `document_units` 表 + ORM + Repo | ✅ 完成 | 唯一约束 `(document_id, sequence_index)` |
| `sections` 表 + ORM + Repo | ✅ 完成 | 自引用 FK `parent_section_id` |
| `chunks` 表 + ORM + Repo | ✅ 完成 | 唯一约束 `(document_unit_id, sequence_index)` |
| `embedding_vectors` 表 + ORM + Repo | ✅ 完成 | `chunk_id UNIQUE`，维度校验 |
| `analysis_results` 表 + ORM + Repo | ✅ 完成 | |
| `chat_sessions` 表 + ORM + Repo | ✅ 完成 | |
| `chat_messages` 表 + ORM + Repo | ✅ 完成 | |
| `SqlAlchemyUnitOfWork` | ✅ 完成 | commit/rollback 管理 |
| sqlite-vec 扩展加载 | ✅ 完成 | 每次连接自动加载，`PRAGMA foreign_keys = ON` |
| **`section_unit_links` 表** | ❌ 缺失 | 实体已定义，无表/模型/仓库 |
| **`workspaces` 表** | ❌ 缺失 | 实体已定义，无表/模型/仓库 |
| **`embedding_index` vec0 虚拟表** | ❌ 缺失 | sqlite-vec 已加载但未创建索引表 |
| **批量 save_batch 方法** | ❌ 缺失 | 所有仓库仅支持单条 upsert |

### 2.3 Parser 输出不一致问题

| Parser | `metadata` 字段 | `parser_name` | `parser_version` |
|--------|:---:|:---:|:---:|
| `PDFParser` | ❌ 缺失 | ❌ 缺失 | ❌ 缺失 |
| `WordParser` | ✅ | ❌ 缺失 | ❌ 缺失 |
| `PptParser` | ✅ | ❌ 缺失 | ❌ 缺失 |
| `TextParser` | ✅ | ❌ 缺失 | ❌ 缺失 |
| `ImageOCRParser` | ✅ | ❌ 缺失 | ❌ 缺失 |

**结论**：所有 Parser 需要统一补充 `parser_name`、`parser_version` 字段；PDFParser 需要补充 `metadata: {"source_type": "pdf", "headings": [], "paragraphs_count": N}`。

---

## 3. PageIndex 数据契约（解析器标准化输出）

### 3.1 统一输出格式

所有 5 个 Parser 的 `parse()` 方法必须返回 `List[PageIndexNode]`，每个节点结构如下：

```python
# PageIndexNode — 标准化解析器输出
{
    # ── 必填字段 ──
    "page_number": int,          # 页码/逻辑序号，从 1 开始
    "content": str,              # 提取的纯文本内容（可为空字符串）
    "char_count": int,           # content 的字符数（len(content)）
    "parser_name": str,          # 解析器类名，如 "PDFParser"（必填，用于追溯）
    "parser_version": str,       # 解析器版本号，如 "1.0.0"（必填，用于追溯）

    # ── 可选但强烈建议的字段 ──
    "metadata": {
        # --- 公共字段（所有 Parser 必须包含）---
        "source_type": str,      # 枚举: "pdf" | "word" | "ppt" | "text" | "image"
        "headings": list,        # Array<{level: int, text: str}>，至少为空数组 []
        "paragraphs_count": int, # 段落数，至少为 0

        # --- WordParser 特有 ---
        "tables_count": int,     # 表格数

        # --- PptParser 特有 ---
        "shapes_count": int,     # 每张 slide 的形状数

        # --- TextParser 特有 ---
        "is_markdown": bool,     # 是否检测到 Markdown 语法

        # --- ImageOCRParser 特有 ---
        "image_format": str,     # "PNG" | "JPEG" | "WEBP"
        "image_width": int,      # 像素宽度
        "image_height": int,     # 像素高度
        "ocr_engine": str,       # "tesseract"
        "ocr_lang": str,         # 语言代码，如 "chi_sim+eng+fra"
        "preprocessing_applied": list[str],  # 已执行的预处理步骤
        "ocr_error": str | None, # OCR 失败时的错误信息（成功时为 None 或不存在）
    }
}
```

### 3.2 各 Parser 的具体约束

#### PDFParser

```python
# 每页输出 1 个节点
{
    "page_number": page_num + 1,
    "content": text,
    "char_count": len(text),
    "parser_name": "PDFParser",
    "parser_version": "1.0.0",
    "metadata": {
        "source_type": "pdf",
        "headings": [],            # PDF 不提取标题（当前能力）
        "paragraphs_count": 0,     # PDF 不统计段落（当前能力）
    }
}
```

**特殊说明**：当前 PDFParser 通过 `page.get_text("text")` 提取纯文本，丢失了段落边界。后续可升级为 `page.get_text("blocks")` 提取段落级信息。

#### WordParser

```python
# 整个文档为 1 个节点
{
    "page_number": 1,
    "content": full_text,
    "char_count": len(full_text),
    "parser_name": "WordParser",
    "parser_version": "1.0.0",
    "metadata": {
        "source_type": "word",
        "headings": [{"level": int, "text": str}, ...],
        "paragraphs_count": len(paragraphs_text),
        "tables_count": len(tables_text),
    }
}
```

**特殊说明**：Word 文档无固定"页"概念，`page_number` 固定为 1。headings 通过 `para.style.name.startswith("Heading")` 识别，level 从 style name 中解析。

#### PptParser

```python
# 每张 slide 输出 1 个节点
{
    "page_number": slide_num,    # 从 1 开始
    "content": clean_text(full_text),
    "char_count": len(full_text),
    "parser_name": "PptParser",
    "parser_version": "1.0.0",
    "metadata": {
        "source_type": "ppt",
        "headings": [{"level": 1, "text": str}, ...],  # idx==0 的占位符识别为标题
        "shapes_count": len(slide.shapes),
        "paragraphs_count": len(slide_texts),
    }
}
```

**特殊说明**：空 PPT（0 张 slide）返回空列表 `[]`。

#### TextParser

```python
# 整个文件为 1 个节点
{
    "page_number": 1,
    "content": clean_text(text),
    "char_count": len(text),
    "parser_name": "TextParser",
    "parser_version": "1.0.0",
    "metadata": {
        "source_type": "text",
        "is_markdown": bool,
        "paragraphs_count": len(paragraphs),
        "headings": [{"level": int, "text": str}, ...],  # 仅 Markdown 文件有值
    }
}
```

**特殊说明**：编码回退链 UTF-8 → GBK → Latin-1（Latin-1 永不失败）。空文件返回 `content: ""`，`char_count: 0`。

#### ImageOCRParser

```python
# 单张图片为 1 个节点
{
    "page_number": 1,
    "content": clean_text(text),   # OCR 失败时为空字符串
    "char_count": len(text),
    "parser_name": "ImageOCRParser",
    "parser_version": "1.0.0",
    "metadata": {
        "source_type": "image",
        "image_format": "PNG",     # 或 "JPEG", "WEBP"
        "image_width": int,
        "image_height": int,
        "ocr_engine": "tesseract",
        "ocr_lang": "chi_sim+eng+fra",
        "preprocessing_applied": ["grayscale", "denoise", "contrast_enhancement"],
        "ocr_error": str | None,   # OCR 失败时包含错误信息；成功时不含此键
    }
}
```

**特殊说明**：无效图片（损坏/非图片格式）抛出 `ValueError("无法解析图片文件")`。OCR 异常不抛，降级为空文本 + `metadata.ocr_error`。

### 3.3 Parser 团队需执行的改动

以下改动在 Parser 团队范围内执行，**不涉及 DB 团队**：

| # | 文件 | 改动内容 | 影响行数 |
|---|------|---------|---------|
| 1 | `parsers/pdf_parser.py` | 每个 PageIndex 节点添加 `"parser_name": "PDFParser"`, `"parser_version": "1.0.0"`, `"metadata": {"source_type": "pdf", "headings": [], "paragraphs_count": 0}` | ~5 行 |
| 2 | `parsers/word_parser.py` | 每个 PageIndex 节点添加 `"parser_name": "WordParser"`, `"parser_version": "1.0.0"` | ~3 行 |
| 3 | `parsers/ppt_parser.py` | 每个 PageIndex 节点添加 `"parser_name": "PptParser"`, `"parser_version": "1.0.0"` | ~3 行 |
| 4 | `parsers/text_parser.py` | 每个 PageIndex 节点添加 `"parser_name": "TextParser"`, `"parser_version": "1.0.0"` | ~3 行 |
| 5 | `parsers/image_ocr_parser.py` | 每个 PageIndex 节点添加 `"parser_name": "ImageOCRParser"`, `"parser_version": "1.0.0"` | ~3 行 |
| 6 | `utils/file_utils.py` | 从 `SUPPORTED_EXTENSIONS` 中移除 `.doc`（US 不支持旧版 Word 格式） | 1 行 |
| 7 | `services/document_ingest_service.py` | Phase 1 改造：实体化 + 事务持久化 | ~30 行 |
| 8 | 所有 5 个 Parser 测试文件 | 更新测试用例的预期输出，增加 parser_name/version 断言 | 每个文件 ~2-5 行 |

---

## 4. 实体填充映射规格（PageIndex → 数据库实体）

以下映射定义了 PageIndex 节点向数据库实体的转换规则。Parser 团队负责在 `DocumentIngestService` 中实现这些映射。

### 4.1 PageIndex[] → DocumentRecord

| DocumentRecord 字段 | 来源 | 取值逻辑 |
|---------------------|------|----------|
| `id` | `str(uuid4())` | 自动生成 |
| `workspace_id` | 外部传入 | API 请求参数 `workspace_id`（由 API 层提供） |
| `title` | `filename` | `Path(filename).stem` |
| `original_filename` | `filename` | 原始文件名（含扩展名） |
| `file_type` | `parsed_pages[0]["metadata"]["source_type"]` + `filename` 扩展名 | 映射规则见 §4.1.1 |
| `file_path` | 系统计算 | `f"data/uploads/{document.id}_{filename}"` |
| `file_hash` | `hashlib.sha256(file_content).hexdigest()` | SHA-256 哈希 |
| `status` | 常量 | `DocumentStatus.PARSED`（一次到位，无中间 UPLOADED） |
| `page_count` | `len(parsed_pages)` | PageIndex 节点数 |
| `created_at` | `datetime.now(timezone.utc)` | |
| `updated_at` | `datetime.now(timezone.utc)` | |

#### 4.1.1 source_type → DocumentFileType 映射表

| `metadata.source_type` | 文件扩展名示例 | `DocumentFileType` | 说明 |
|------------------------|--------------|---------------------|------|
| `"pdf"` | `.pdf` | `PDF` | |
| `"word"` | `.docx` | `DOCX` | |
| `"ppt"` | `.pptx` | `PPTX` | |
| `"text"` | `.txt` | `TEXT` | |
| `"text"` | `.md` | `TEXT` | Markdown 归类为 TEXT |
| `"image"` | `.jpg`, `.jpeg` | `IMAGE` | |
| `"image"` | `.png` | `IMAGE` | |
| `"image"` | `.webp` | `IMAGE` | |

### 4.2 PageIndex[𝑖] → DocumentUnit

| DocumentUnit 字段 | 来源 | 取值逻辑 |
|-------------------|------|----------|
| `id` | `str(uuid4())` | 自动生成 |
| `document_id` | `DocumentRecord.id` | FK 关联 |
| `sequence_index` | 数组索引 `𝑖` | 0, 1, 2, … |
| `text_content` | `node["content"]` | |
| `page_number` | `node["page_number"]` | |
| `start_char` | — | 留 `None`（此粒度下不适用，由 Chunk 层填充） |
| `end_char` | — | 留 `None`（同上） |
| `token_count` | `node["char_count"]` | ⚠️ 暂用 char_count 近似，后续 `token_utils` 实现后替换 |
| `metadata_json` | `node["metadata"]` | 整个 dict |
| `raw_content_json` | 整个 `node` | 完整原始 PageIndex 节点，用于审计追溯 |
| `parser_name` | `node["parser_name"]` | |
| `parser_version` | `node["parser_version"]` | |
| `external_id` | — | 留 `None`，预留外部系统 ID |
| `created_at` | `datetime.now(timezone.utc)` | |

### 4.3 PageIndex[] + headings → Section[] + SectionUnitLink[]

*（Phase 2 实现，以下为预设计）*

**触发条件**：仅对 WordParser（有 headings）和 TextParser（Markdown 且有 headings）的解析结果执行章节构建。PDF/Ppt/Image 的第一版不做章节提取。

| Section 字段 | 来源 |
|--------------|------|
| `id` | `str(uuid4())` |
| `document_id` | `DocumentRecord.id` |
| `parent_section_id` | 根据 heading level 层级关系计算：level N 的 section 的 parent 为最近的前一个 level N-1 heading |
| `title` | `heading["text"]` |
| `level` | `heading["level"]` |
| `order_index` | heading 在全部 headings 中的出现顺序（从 0 起） |
| `start_page` | 该 heading 首次出现的 page_number（对于 DOCX/TXT 固定为 1） |
| `end_page` | 下一个同级或上级 heading 出现前的 page_number |
| `summary` | 留 `None`（后续 AI 生成） |
| `metadata_json` | `{"heading_text": heading["text"], "source": source_type}` |
| `parser_name` / `parser_version` | 来自 PageIndex 节点 |

| SectionUnitLink 字段 | 来源 |
|---------------------|------|
| `id` | `str(uuid4())` |
| `section_id` | `Section.id` |
| `document_unit_id` | 该 Section 覆盖范围内的所有 `DocumentUnit.id` |
| `order_index` | 该 Unit 在 Section 内的自然顺序 |

### 4.4 DocumentUnit → Chunk[]

*（Phase 3 实现，以下为预设计）*

Chunk 切分由独立的 `ChunkService` 负责，Parser 层不直接生成 Chunk。DB 团队只需确保 `chunks` 表结构就绪即可。

| Chunk 字段 | 来源 |
|------------|------|
| `id` | `str(uuid4())` |
| `document_unit_id` | 父 `DocumentUnit.id` |
| `sequence_index` | Chunk 在父 Unit 内的序号（0 起） |
| `text_content` | 切分后的文本片段 |
| `start_char` | 在父 Unit.text_content 中的字符起始偏移 |
| `end_char` | 在父 Unit.text_content 中的字符结束偏移 |
| `token_count` | 实际 token 数 |
| `chunker_name` | 切分器标识，如 `"fixed_size_chunker"` / `"recursive_chunker"` |
| `chunker_version` | 切分器版本号 |
| `metadata_json` | 切分元数据（chunk_size, overlap_size 等） |
| `embedding_model` | 留 `None`（由 `EmbeddingService` 后续填充） |
| `embedding_dimension` | 留 `None`（同上） |
| `embedding_created_at` | 留 `None`（同上） |

---

## 5. 数据库缺失清单

以下列出的项目由 **Database 团队** 负责实现。

### 5.1 阻断级缺失（P0 — 必须立即补齐）

#### 5.1.1 `section_unit_links` 表

> **对应实体**：[`SectionUnitLink`](backend-python/app/entities/section_unit_link.py:6)

**SQL（加入 `init_db.py` 的 `_create_schema()`）**：

```sql
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

**ORM 模型（加入 `db/models.py`）**：

```python
class SectionUnitLinkModel(Base):
    __tablename__ = "section_unit_links"
    __table_args__ = (
        UniqueConstraint("section_id", "document_unit_id"),
        UniqueConstraint("section_id", "order_index"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    section_id: Mapped[str] = mapped_column(
        ForeignKey("sections.id"), nullable=False
    )
    document_unit_id: Mapped[str] = mapped_column(
        ForeignKey("document_units.id"), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
```

**Repository（新增 `repositories/section_unit_link_repository.py`）**：

```python
class SectionUnitLinkRepository:
    """参照 SectionRepository 的 upsert 模式实现。"""
    def save(self, link: SectionUnitLink) -> SectionUnitLink: ...
    def save_batch(self, links: list[SectionUnitLink]) -> list[SectionUnitLink]: ...
    def get_by_section_id(self, section_id: str) -> list[SectionUnitLink]: ...
    def get_by_id(self, link_id: str) -> SectionUnitLink | None: ...
```

**唯一约束说明**：
- `UNIQUE(section_id, document_unit_id)`：同一 Section 内不能重复关联同一 DocumentUnit
- `UNIQUE(section_id, order_index)`：同一 Section 内不能有两个相同排序位置

#### 5.1.2 仓库批量操作接口

每个仓库新增 `save_batch` 方法：

```python
# repositories/document_unit_repository.py
class DocumentUnitRepository:
    def save_batch(self, units: list[DocumentUnit]) -> list[DocumentUnit]:
        """批量 upsert。复用单条 save 逻辑，但不逐条 flush。"""
        for unit in units:
            self.save(unit)
        return units

# repositories/chunk_repository.py
class ChunkRepository:
    def save_batch(self, chunks: list[Chunk]) -> list[Chunk]: ...

# repositories/section_repository.py
class SectionRepository:
    def save_batch(self, sections: list[Section]) -> list[Section]: ...
```

**实现说明**：
- `save_batch` 调用方负责 flush + commit（通常在 `UnitOfWork.commit()` 中完成）
- 所有单条 `save()` 方法已有的唯一约束和外键约束在批量场景下自动生效

---

### 5.2 重要缺失（P1 — Phase 2/3 前补足）

#### 5.2.1 `workspaces` 表

```sql
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    type TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

对应 ORM 模型和 Repository 按现有模式实现。完成后，`document_records.workspace_id` 可以添加外键约束。

#### 5.2.2 `embedding_index` 向量虚拟表（sqlite-vec vec0）

**⚠️ 当前状态**：sqlite-vec 扩展已加载，`embedding_vectors` 表仅以 JSON 文本存储向量，无法高效搜索。

**Python 加载方式升级建议**：

当前代码使用 `load_extension("sqlite_vec")` [init_db.py:20-23](backend-python/app/db/init_db.py:20)。sqlite-vec 官方推荐使用 Python binding：

```python
# 旧方式（当前代码）
connection.load_extension("sqlite_vec")

# 新方式（官方推荐）
import sqlite_vec
sqlite_vec.load(connection)
```

**vec0 虚拟表创建**（在 `_create_schema()` 中的 `CREATE TABLE` 块之后）：

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS embedding_index USING vec0(
    embedding float[{EMBEDDING_DIMENSION}],
    chunk_id TEXT,
    embedding_model TEXT,
    created_at TEXT
);
```

**双表策略**：
- `embedding_vectors`（关系表）：存储元数据（chunk_id, model, dimension, created_at）+ 向量 JSON 副本
- `embedding_index`（vec0 虚拟表）：专门用于 KNN 向量搜索，存储 BLOB 格式的 float32 向量

**向量检索查询模板**：

```sql
SELECT
    ei.rowid,
    ei.chunk_id,
    ei.distance
FROM embedding_index AS ei
WHERE ei.embedding MATCH ?
ORDER BY ei.distance
LIMIT ?
```

**Python 中序列化向量**（使用 sqlite-vec 官方方法）：

```python
from sqlite_vec import serialize_float32

vector = [0.1, 0.2, 0.3, ...]  # list[float]
blob = serialize_float32(vector)
# 然后 bind 到 SQL 参数中
```

**`EmbeddingRepository` 需新增方法**：

```python
class EmbeddingRepository:
    # ... 现有方法保持不变 ...

    def search_similar(
        self,
        *,
        query_vector: list[float],
        top_k: int = 10,
        embedding_model: str | None = None,
    ) -> list[ChunkEmbedding]:
        """
        KNN 向量相似度搜索。
        :param query_vector: 查询向量 (list[float])
        :param top_k: 返回结果数
        :param embedding_model: 可选，按模型过滤
        :return: 按距离排序的 ChunkEmbedding 列表
        """
```

---

## 6. Repository 接口契约

以下是 Parser 层（注入服务）对 DB 层（仓库）的完整接口契约。DB 团队需确保这些方法签名可被调用。

### 6.1 接口清单

```python
# ─── 已有，直接可用 ─────────────────────────

class DocumentRepository:
    def save(self, document: DocumentRecord) -> DocumentRecord: ...
    def get_by_id(self, document_id: str) -> DocumentRecord | None: ...

class DocumentUnitRepository:
    def save(self, unit: DocumentUnit) -> DocumentUnit: ...
    def save_batch(self, units: list[DocumentUnit]) -> list[DocumentUnit]: ...  # ← 需新增
    def get_by_id(self, unit_id: str) -> DocumentUnit | None: ...

class ChunkRepository:
    def save(self, chunk: Chunk) -> Chunk: ...
    def save_batch(self, chunks: list[Chunk]) -> list[Chunk]: ...              # ← 需新增
    def get_by_id(self, chunk_id: str) -> Chunk | None: ...

class SectionRepository:
    def save(self, section: Section) -> Section: ...
    def save_batch(self, sections: list[Section]) -> list[Section]: ...        # ← 需新增
    def get_by_id(self, section_id: str) -> Section | None: ...

class SectionUnitLinkRepository:                                                # ← 整类需新增
    def save(self, link: SectionUnitLink) -> SectionUnitLink: ...
    def save_batch(self, links: list[SectionUnitLink]) -> list[SectionUnitLink]: ...
    def get_by_section_id(self, section_id: str) -> list[SectionUnitLink]: ...
    def get_by_id(self, link_id: str) -> SectionUnitLink | None: ...

class EmbeddingRepository:
    def save_for_chunk(self, *, chunk_id, embedding_model, vector) -> ChunkEmbedding: ...
    def get_by_chunk_id(self, chunk_id: str) -> ChunkEmbedding | None: ...
    def search_similar(                                                        # ← 需新增
        self, *, query_vector: list[float], top_k: int = 10
    ) -> list[ChunkEmbedding]: ...
```

### 6.2 语义约束

| 约束 | 适用范围 | 说明 |
|------|---------|------|
| **幂等性** | 所有 `save()` | 同 ID 第二次调用 = UPDATE（不应抛错） |
| **不自动提交** | 所有方法 | `Session` 的 commit/rollback 统一由 `SqlAlchemyUnitOfWork` 管理 |
| **NULL 安全** | `get_by_id()` | 记录不存在返回 `None`，不抛异常 |
| **外键校验** | `save()` | 依赖 `PRAGMA foreign_keys = ON`，写入非法 FK 值时由 SQLite 拒绝 |
| **唯一约束** | `save_batch()` | 批量写入违反唯一约束时，整体事务回滚 |

### 6.3 测试要求

DB 团队需为以下场景编写集成测试（参照 [`test_sqlite_repositories.py`](backend-python/tests/test_sqlite_repositories.py:83) 的模式）：

- `test_section_unit_link_save_and_retrieve` — 基本 CRUD
- `test_section_unit_link_unique_violation` — 同 Section 内重复关联应报错
- `test_section_unit_link_cascade` — 删除 Section 后关联记录的行为
- `test_batch_save_document_units` — 批量 upsert 性能与正确性
- `test_embedding_index_search` — vec0 虚拟表 KNN 检索功能
- `test_embedding_dimension_mismatch` — 向量维度不匹配应报错

---

## 7. 安全摄入流水线设计

### 7.1 改造后的 `DocumentIngestService`

```python
import hashlib
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

from app.entities import DocumentRecord, DocumentUnit
from app.enums import DocumentFileType, DocumentStatus
from app.parsers.parser_factory import ParserFactory
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.db.unit_of_work import SqlAlchemyUnitOfWork


# source_type → DocumentFileType 映射
SOURCE_TYPE_TO_FILE_TYPE = {
    "pdf": DocumentFileType.PDF,
    "word": DocumentFileType.DOCX,
    "ppt": DocumentFileType.PPTX,
    "text": DocumentFileType.TEXT,
    "image": DocumentFileType.IMAGE,
}


class DocumentIngestService:
    """
    安全文档摄取流水线：
    Step 1 — 解析（纯计算，不涉及 DB）
    Step 2 — 构建实体（纯内存，不涉及 DB）
    Step 3 — 事务持久化（全部或全不）
    """

    async def ingest_document(
        self,
        *,
        filename: str,
        file_content: bytes,
        workspace_id: str,
        uow_factory,  # Callable[[], SqlAlchemyUnitOfWork]
    ) -> dict:
        # ── Step 1: 解析 ──
        parser = ParserFactory.get_parser(filename)
        parsed_pages = parser.parse(file_content)

        if not parsed_pages:
            raise ValueError(f"解析结果为空: {filename}")

        source_type = parsed_pages[0]["metadata"]["source_type"]
        file_type = SOURCE_TYPE_TO_FILE_TYPE.get(
            source_type, DocumentFileType.OTHER
        )

        # ── Step 2: 构建实体 ──
        file_hash = hashlib.sha256(file_content).hexdigest()
        document_id = str(uuid4())

        document = DocumentRecord(
            id=document_id,
            workspace_id=workspace_id,
            title=Path(filename).stem,
            original_filename=filename,
            file_type=file_type,
            file_path=f"data/uploads/{document_id}_{filename}",
            file_hash=file_hash,
            status=DocumentStatus.PARSED,
            page_count=len(parsed_pages),
        )

        units = []
        for i, page in enumerate(parsed_pages):
            unit = DocumentUnit(
                document_id=document_id,
                sequence_index=i,
                text_content=page["content"],
                page_number=page["page_number"],
                token_count=page["char_count"],  # 暂用字符数近似
                metadata_json=page.get("metadata"),
                raw_content_json=page,
                parser_name=page.get("parser_name"),
                parser_version=page.get("parser_version"),
            )
            units.append(unit)

        # ── Step 3: 事务持久化 ──
        with uow_factory() as uow:
            try:
                DocumentRepository(uow.session).save(document)
                DocumentUnitRepository(uow.session).save_batch(units)
                uow.commit()
            except Exception:
                # 回滚由 uow.__exit__ 自动处理
                raise

        # 返回给 API 层
        return {
            "filename": filename,
            "document_id": document_id,
            "total_pages": len(parsed_pages),
            "status": "parsed_successfully",
            "page_index_preview": [
                {
                    "page_number": p["page_number"],
                    "char_count": p["char_count"],
                    "source_type": source_type,
                }
                for p in parsed_pages
            ],
        }
```

### 7.2 事务边界

```
          ┌──────────────────────────────┐
          │  uow_factory() 创建 Session    │
          │  ↓                            │
          │  DocumentRepository.save()     │
          │  DocumentUnitRepository        │
          │      .save_batch()             │
          │  ↓                            │
          │  uow.commit()                  │
          │  ── 成功 → 数据永久化           │
          │  ── 失败 → uow.__exit__        │
          │           自动 rollback()       │
          └──────────────────────────────┘
```

### 7.3 API 层适配

`DocumentController.upload_document` 需要传入 `workspace_id` 和 `uow_factory` 依赖：

```python
# document_controller.py 的改造要点：
# 1. 接收 workspace_id（来自请求体或查询参数）
# 2. 注入 uow_factory（通过 FastAPI Depends）
# 3. 将 uow_factory 传递给 ingest_document
```

---

## 8. 状态机与生命周期

### 8.1 文档状态流转

```
         ┌──────────┐
         │ UPLOADED │  ← 仅上传未解析（当前流水线跳过此状态，直接→PARSED）
         └────┬─────┘
              │
    ┌─────────▼─────────┐
    │      PARSED       │  ← 解析完成，DocumentUnit 已持久化
    └─────────┬─────────┘
              │
    ┌─────────▼─────────┐
    │     INDEXED       │  ← Chunk + Embedding 全部完成
    └───────────────────┘

    任一阶段失败 → FAILED（事务回滚，状态标记为失败）
```

### 8.2 状态含义

| 状态 | 含义 | 数据库中对应的写入 |
|------|------|-------------------|
| `UPLOADED` | 文件已接收 | `DocumentRecord` 已创建（file_path, file_hash 已填） |
| `PARSED` | 解析完成 | 上述 + `DocumentUnit[]` 已创建 |
| `INDEXED` | RAG 就绪 | 上述 + `Chunk[]` + `EmbeddingVector[]` + vec0 索引 |
| `FAILED` | 处理失败 | 仅 `DocumentRecord`（如有），事务已回滚 |

### 8.3 当前实现策略

Phase 1（当前阶段）不经过 `UPLOADED` 中间态，直接在解析成功后创建 `DocumentRecord` 并设 `status=PARSED`。这样简化了控制器的事务逻辑（一次 commit）。

---

## 9. 安全设计矩阵

### 9.1 数据完整性

| 层面 | 措施 | 当前状态 | 位置 |
|------|------|---------|------|
| 外键级联 | `PRAGMA foreign_keys = ON` | ✅ 已实现 | [orm.py:24](backend-python/app/db/orm.py:24) |
| Chunk → DocumentUnit FK | `chunks.document_unit_id → document_units.id` | ✅ 已实现 | [models.py:87](backend-python/app/db/models.py:87) |
| Embedding → Chunk FK | `embedding_vectors.chunk_id → chunks.id` | ✅ 已实现 | [models.py:186](backend-python/app/db/models.py:186) |
| Section → Section FK | `sections.parent_section_id → sections.id` | ✅ 已实现 | [models.py:82](backend-python/app/db/models.py:82) |
| DocumentUnit 唯一约束 | `UNIQUE(document_id, sequence_index)` | ✅ 已实现 | [models.py:28](backend-python/app/db/models.py:28) |
| Chunk 唯一约束 | `UNIQUE(document_unit_id, sequence_index)` | ✅ 已实现 | [models.py:87](backend-python/app/db/models.py:87) |
| Embedding 唯一约束 | `UNIQUE(chunk_id)` | ✅ 已实现 | [models.py:186](backend-python/app/db/models.py:186) |
| 向量维度校验 | `EmbeddingRepository` 保存前检查 | ✅ 已实现 | [embedding_repository.py:47](backend-python/app/repositories/embedding_repository.py:47) |
| Chunk 存在性校验 | 保存 Embedding 前验证 Chunk 存在 | ✅ 已实现 | [embedding_repository.py:50](backend-python/app/repositories/embedding_repository.py:50) |
| 事务原子性 | `SqlAlchemyUnitOfWork` 包裹 | ✅ 已实现 | [unit_of_work.py:5](backend-python/app/db/unit_of_work.py:5) |
| SectionUnitLink 唯一约束 | `UNIQUE(section_id, document_unit_id)` + `UNIQUE(section_id, order_index)` | ❌ 待实现 | DB 团队 P0 |

### 9.2 输入安全

| 风险 | 措施 | 位置 |
|------|------|------|
| 文件名路径穿越 | `file_path` 由 `f"data/uploads/{uuid}_{filename}"` 生成，filename 经 FastAPI `UploadFile.filename` 获取（不含路径） | Service 层 |
| 超大文件 DOS | FastAPI 默认请求体大小限制；`ImagePreprocessor` 限制图片尺寸 ≤ 4096×4096 | 框架 + 预处理层 |
| 恶意二进制注入 DB | `text_content` 为纯文本字符串，SQLAlchemy 参数化查询防注入 | ORM 层 |
| JSON 字段注入 | `metadata_json` 和 `raw_content_json` 通过 `json.dumps()` 序列化后存储为 TEXT，读时 `json.loads()` 反序列化 | `sqlite_helpers.py` |
| parser_name 伪造 | 值由 Parser 代码硬编码设置，不接受外部输入 | Parser 层 |
| 文件哈希冲突 | SHA-256 碰撞概率可忽略不计 | Service 层 |

### 9.3 错误恢复

| 场景 | 行为 |
|------|------|
| 解析成功，DB 写入失败 | `uow.__exit__` 自动 rollback，无残留数据 |
| 解析失败 | 不进入 DB 操作，直接向上抛异常，API 转 400/500 |
| DB 连接断开 | SQLAlchemy 连接池 + `uow.__exit__` rollback |
| 中途服务重启 | 数据库无未提交事务（SQLite WAL 模式自动恢复） |

---

## 10. 团队职责与交付边界

### 10.1 耦合点总结

```
┌─────────────────────────────────────────────────┐
│                Parser 团队                        │
│                                                  │
│  parsers/*.py         (5 个 Parser)              │
│  parser_factory.py    (路由工厂)                  │
│  services/document_ingest_service.py  (流水线)    │
│  utils/text_utils.py  (文本工具)                  │
│  utils/file_utils.py  (文件工具)                  │
│                                                  │
│  产出: 标准化的 PageIndex List[Dict]               │
│        实体构建逻辑 (DocumentRecord/Unit)          │
│        事务编排 (调用 UnitOfWork + Repository)     │
│                                                  │
├──────────────────────────┬──────────────────────┤
│                          │                       │
│    共享：app/entities/   │   共享：app/db/orm.py  │
│    (Pydantic 模型定义)   │   (SessionFactory)     │
│                          │                       │
├──────────────────────────┴──────────────────────┤
│                Database 团队                      │
│                                                  │
│  db/models.py          (SQLAlchemy ORM)          │
│  db/init_db.py         (SQL + vec0 虚拟表)       │
│  db/orm.py             (连接工厂)                 │
│  db/unit_of_work.py    (事务管理)                 │
│  repositories/*.py     (9 个 Repository)          │
│  repositories/sqlite_helpers.py  (序列化工具)     │
│                                                  │
│  产出: 表定义 + ORM 模型                          │
│        Repository CRUD + save_batch              │
│        sqlite-vec 向量索引                        │
│        事务管理基础设施                             │
└─────────────────────────────────────────────────┘
```

### 10.2 交付物清单

#### Parser 团队交付物

| # | 交付物 | 格式 | 优先级 | 截止 |
|---|--------|------|--------|------|
| 1 | 5 个 Parser 补全 `parser_name`/`parser_version`/`metadata` 字段 | 代码 | P0 | Phase 1 |
| 2 | `file_utils.py` 移除 `.doc` | 代码 | P0 | Phase 1 |
| 3 | `DocumentIngestService` 接入事务（Phase 1 版） | 代码 | P0 | Phase 1 |
| 4 | 更新所有 Parser 测试用例 | 代码 | P0 | Phase 1 |
| 5 | 本规格文档 | Markdown | P0 | Phase 1 |
| 6 | 集成测试（Parser → DB 端到端） | 代码 | P1 | Phase 2 |

#### Database 团队交付物

| # | 交付物 | 格式 | 优先级 | 截止 |
|---|--------|------|--------|------|
| 1 | `section_unit_links` 表 + ORM + Repository | 代码 | P0 | Phase 1 |
| 2 | 所有 Repository 增加 `save_batch()` | 代码 | P0 | Phase 1 |
| 3 | `SectionUnitLinkRepository` 单元测试 | 代码 | P0 | Phase 1 |
| 4 | `workspaces` 表 + ORM + Repository | 代码 | P1 | Phase 2 |
| 5 | `embedding_index` vec0 虚拟表 + `EmbeddingRepository.search_similar()` | 代码 | P1 | Phase 3 |
| 6 | sqlite-vec 加载方式升级（`load_extension` → `sqlite_vec.load()`） | 代码 | P1 | Phase 3 |
| 7 | 批量操作集成测试 | 代码 | P1 | Phase 2 |

---

## 11. 实施路线图

### Phase 1：基础衔接（当前 → 2 周）

**目标**：Parser 输出标准化 + 基础实体可持久化

```
Parser 团队:
  1. 全部 5 个 Parser 补 parser_name/parser_version/metadata     [1 天]
  2. file_utils.py 移除 .doc                                        [0.5 天]
  3. 更新对应测试用例，确保 100% 通过                               [0.5 天]
  4. DocumentIngestService 接入事务，实现 Phase 1 流水线            [1 天]

Database 团队:
  1. section_unit_links 表 + ORM + Repository                      [1 天]
  2. DocumentUnitRepository/ChunkRepository/SectionRepository
     增加 save_batch()                                              [1 天]
  3. 单元测试补全                                                    [0.5 天]

联调:
  1. Parser + DB 集成测试：上传 → 解析 → DocumentRecord
     + DocumentUnit 入库 → 验证持久化                               [0.5 天]
```

**Phase 1 验收标准**：

- [ ] Parser 团队：所有 122 个现有测试 + 新增测试 100% 绿灯
- [ ] Database 团队：`SectionUnitLinkRepository` 完整 CRUD 测试通过
- [ ] 联调：上传 PDF/DOCX/PPTX/TXT/Image → DB 中有对应的 `DocumentRecord` + `DocumentUnit` 记录
- [ ] 联调：违反唯一约束时事务正确回滚

### Phase 2：章节化（2 周后）

**目标**：Section 自动构建 + SectionUnitLink 关联

```
Parser 团队:
  1. 实现 SectionService（从 headings 构建 Section 树）              [2 天]
  2. 在 DocumentIngestService 中加入 Section 构建 + 持久化步骤      [1 天]
  3. 集成测试                                                        [1 天]

Database 团队:
  1. workspaces 表 + ORM + Repository                               [1 天]
  2. 外键约束补齐（document_records.workspace_id → workspaces.id）  [0.5 天]
```

**Phase 2 验收标准**：

- [ ] 上传含 Headings 的 DOCX/MD 文件 → DB 中 Section 层级正确
- [ ] `section_unit_links` 关联记录正确

### Phase 3：RAG 向量化（4 周后）

**目标**：Chunk 切分 + Embedding 生成 + 向量搜索

```
取决于:
  - ChunkService 实现
  - EmbeddingService 实现
  - Database 团队完成 vec0 虚拟表 + search_similar()
```

---

## 12. 测试要求

### 12.1 Parser 层测试

| 测试类型 | 要求 | 现有状态 |
|---------|------|---------|
| 单元测试 | 每个 Parser 独立测试，mock 外部依赖 | ✅ 122 个测试全绿 |
| 契约测试 | 验证每个 Parser 输出符合 PageIndex 数据契约 | ❌ 需新增（基于 §3 的契约） |
| 边界测试 | 空文件、超大文件、损坏文件、OCR 失败 | ✅ 已覆盖 |

**需新增的契约测试**（Parser 团队）：

```python
# tests/test_parser_output_contract.py
@pytest.mark.parametrize("parser_class,expected_source_type", [
    (PDFParser, "pdf"),
    (WordParser, "word"),
    (PptParser, "ppt"),
    (TextParser, "text"),
    (ImageOCRParser, "image"),
])
def test_parser_output_conforms_to_pageindex_contract(parser_class, expected_source_type):
    """验证每个 Parser 的输出符合标准 PageIndex 契约。"""
    # 每个字段的 type 和存在性校验
    ...
```

### 12.2 集成测试

| 测试场景 | 描述 |
|---------|------|
| `test_ingest_pdf_persists` | PDF 上传 → DocumentRecord + N 个 DocumentUnit 入库 |
| `test_ingest_docx_persists` | DOCX 上传 → 1 个 DocumentUnit，metadata 含 headings |
| `test_duplicate_upload_idempotent` | 同一文件两次上传 → 第二次为 upsert（不抛错） |
| `test_transaction_rollback_on_error` | 中途抛异常 → DB 无残留数据 |
| `test_section_unit_link_unique` | 重复关联抛错 |

### 12.3 运行命令

```bash
# Parser 层测试（当前全绿）
cd backend-python
python -m pytest tests/test_parser_factory.py tests/test_pdf_parser.py \
  tests/test_word_parser.py tests/test_ppt_parser.py tests/test_text_parser.py \
  tests/test_image_ocr_parser.py tests/test_image_preprocessor.py \
  tests/test_document_controller.py tests/test_document_ingest_service.py \
  tests/test_file_utils.py tests/test_text_utils.py -v

# Database 层测试
python -m pytest tests/test_sqlite_repositories.py \
  tests/test_sqlalchemy_persistence.py \
  tests/test_database_initialization.py -v

# 全量测试
python -m pytest tests/ -v --tb=short
```

---

## 13. 附录

### 13.1 术语对照表

| 简写 | 全称 | 说明 |
|------|------|------|
| US | User Story | 用户故事 |
| FK | Foreign Key | 外键约束 |
| UK | Unique Constraint | 唯一约束 |
| OCP | Open-Closed Principle | 开闭原则 |
| UoW | Unit of Work | 工作单元（事务管理模式） |
| KNN | K-Nearest Neighbors | K 近邻搜索 |
| vec0 | sqlite-vec virtual table | sqlite-vec 的向量索引虚拟表类型 |
| BLOB | Binary Large Object | 二进制大对象（sqlite-vec 的向量存储格式） |

### 13.2 文件索引

| 文件 | 描述 | 团队 |
|------|------|------|
| `app/parsers/pdf_parser.py` | PDF 解析器 | Parser |
| `app/parsers/word_parser.py` | Word 解析器 | Parser |
| `app/parsers/ppt_parser.py` | PPT 解析器 | Parser |
| `app/parsers/text_parser.py` | 纯文本/Markdown 解析器 | Parser |
| `app/parsers/image_ocr_parser.py` | 图片 OCR 解析器 | Parser |
| `app/parsers/image_preprocessor.py` | 图片预处理器 | Parser |
| `app/parsers/parser_factory.py` | 解析器工厂 | Parser |
| `app/services/document_ingest_service.py` | 摄取流水线服务 | Parser |
| `app/api/document_controller.py` | 上传 API 控制器 | Parser |
| `app/utils/file_utils.py` | 文件工具 | Parser |
| `app/utils/text_utils.py` | 文本工具 | Parser |
| `app/entities/*.py` | Pydantic 实体定义 | **共享** |
| `app/db/init_db.py` | SQL schema + 扩展加载 | Database |
| `app/db/models.py` | SQLAlchemy ORM 模型 | Database |
| `app/db/orm.py` | 连接工厂 + SessionFactory | Database |
| `app/db/unit_of_work.py` | 事务管理 | Database |
| `app/repositories/*.py` | 仓库接口实现 | Database |
| `app/repositories/sqlite_helpers.py` | JSON/DateTime 序列化 | Database |
| `app/rag/*.py` | RAG 检索/重排/上下文 | Database（Phase 3） |

### 13.3 参考链接

- [sqlite-vec GitHub](https://github.com/asg017/sqlite-vec) — 向量搜索 SQLite 扩展
- [sqlite-vec Python 文档](https://alexgarcia.xyz/sqlite-vec/python.html) — Python 绑定用法
- [US #25](https://github.com/GreenBeanICE/greenbean-study-assistant/issues/25) — 对应的 User Story
- [AGENTS.md](../../AGENTS.md) — 项目整体说明

---

> **文档维护**：本文档由 Parser 团队和 Database 团队共同维护。任何一方发现不一致或需要修订时，通过 PR 更新本文档并通知对侧团队 review。

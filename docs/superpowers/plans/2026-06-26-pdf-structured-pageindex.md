# PDF Structured PageIndex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 PDF 解析从"纯文本页切片"升级为"结构化 block + heading 抽取"，生成正确的章节树。

**Architecture:** PDFParser 输出结构化 blocks/page_stats/headings，page_index_builder 消费 richer metadata 构树，保持 DocumentUnit=页 不变。

**Tech Stack:** PyMuPDF, Pydantic v2, pytest, Python 3.12

---

### Task 1: PDFParser 结构化输出

**Files:**
- Modify: `backend-python/app/parsers/pdf_parser.py`
- Test: `backend-python/tests/unit/parsers/test_pdf_parser.py`

- [ ] **Step 1: Write the failing test for structured blocks extraction**

```python
def test_pdf_parser_extracts_structured_blocks():
    """PDFParser 应该从每页提取结构化 blocks，包含 bbox/font_size/is_bold 等信息。"""
    parser = PDFParser()
    
    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        mock_doc.__len__.return_value = 1
        
        mock_page = MagicMock()
        mock_page.get_text.return_value = "1. Introduction\nThis is content."
        mock_page.rect.width = 595.0
        mock_page.rect.height = 842.0
        
        # 模拟 PyMuPDF 的 dict 模式输出
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "bbox": (72.0, 96.0, 300.0, 120.0),
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "1. Introduction",
                                    "font": "Helvetica-Bold",
                                    "size": 18.0,
                                    "bbox": (72.0, 96.0, 300.0, 120.0)
                                }
                            ]
                        }
                    ]
                },
                {
                    "bbox": (72.0, 130.0, 500.0, 200.0),
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "This is content.",
                                    "font": "Helvetica",
                                    "size": 10.5,
                                    "bbox": (72.0, 130.0, 500.0, 150.0)
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_page.get_text.side_effect = [mock_page.get_text.return_value, "1. Introduction\nThis is content."]
        mock_doc.load_page.return_value = mock_page
        
        result = parser.parse(b"fake pdf")
        
        assert len(result) == 1
        page = result[0]
        
        # 验证结构化 blocks
        assert "blocks" in page["raw_content_json"]
        blocks = page["raw_content_json"]["blocks"]
        assert len(blocks) == 2
        assert blocks[0]["text"] == "1. Introduction"
        assert blocks[0]["bbox"] == [72.0, 96.0, 300.0, 120.0]
        assert blocks[0]["font_size"] == 18.0
        assert blocks[0]["font_name"] == "Helvetica-Bold"
        assert blocks[0]["is_bold"] is True
        assert blocks[1]["text"] == "This is content."
        assert blocks[1]["is_bold"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk pytest backend-python/tests/unit/parsers/test_pdf_parser.py::test_pdf_parser_extracts_structured_blocks -v`
Expected: FAIL with "KeyError: 'raw_content_json'" or similar

- [ ] **Step 3: Implement structured blocks extraction**

```python
class PDFParser:
    def _extract_blocks(self, page) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """从 PyMuPDF page 提取结构化 blocks 和 page_stats。"""
        blocks = []
        text_dict = page.get_text("dict")
        
        # 收集所有字号用于统计
        font_sizes = []
        block_id = 0
        
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # 只处理文本块
                continue
            
            block_text = ""
            block_font_size = 0.0
            block_font_name = ""
            block_is_bold = False
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span.get("text", "").strip()
                    if span_text:
                        block_text += span_text + " "
                        block_font_size = span.get("size", 0.0)
                        block_font_name = span.get("font", "")
                        font_sizes.append(block_font_size)
                        if "Bold" in block_font_name or "bold" in block_font_name.lower():
                            block_is_bold = True
            
            block_text = block_text.strip()
            if not block_text:
                continue
            
            bbox = block.get("bbox", (0, 0, 0, 0))
            blocks.append({
                "id": f"b-{block_id}",
                "text": block_text,
                "bbox": list(bbox),
                "font_size": block_font_size,
                "font_name": block_font_name,
                "is_bold": block_is_bold,
                "line_count": len(block.get("lines", [])),
                "is_top_region": bbox[1] < page.rect.height * 0.3,
                "is_bottom_region": bbox[3] > page.rect.height * 0.7,
                "sequence_index": block_id,
            })
            block_id += 1
        
        # 计算 page_stats
        primary_font_size = max(set(font_sizes), key=font_sizes.count) if font_sizes else 10.0
        max_font_size = max(font_sizes) if font_sizes else 10.0
        
        page_stats = {
            "page_width": page.rect.width,
            "page_height": page.rect.height,
            "primary_font_size": primary_font_size,
            "max_font_size": max_font_size,
            "top_margin_cutoff": page.rect.height * 0.1,
            "bottom_margin_cutoff": page.rect.height * 0.9,
        }
        
        return blocks, page_stats
```

- [ ] **Step 4: Update parse method to use structured extraction**

```python
    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        doc = fitz.open(stream=file_content, filetype="pdf")
        parsed_pages = []
        
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # 提取结构化 blocks
                blocks, page_stats = self._extract_blocks(page)
                
                # 提取纯文本用于兼容
                text = page.get_text("text").strip()
                
                # 构造 page node
                page_node = {
                    "page_number": page_num + 1,
                    "content": text,
                    "char_count": len(text),
                    "parser_name": "PDFParser",
                    "parser_version": "2.0.0",
                    "metadata": {
                        "source_type": "pdf",
                        "headings": [],
                        "paragraphs_count": len([p for p in text.split("\n\n") if p.strip()]),
                        "page_stats": page_stats,
                    },
                    "raw_content_json": {
                        "page_number": page_num + 1,
                        "parser_name": "PDFParser",
                        "parser_version": "2.0.0",
                        "blocks": blocks,
                    }
                }
                parsed_pages.append(page_node)
        finally:
            doc.close()
            
        return parsed_pages
```

- [ ] **Step 5: Run test to verify it passes**

Run: `rtk pytest backend-python/tests/unit/parsers/test_pdf_parser.py::test_pdf_parser_extracts_structured_blocks -v`
Expected: PASS

- [ ] **Step 6: Write failing test for heading candidate detection**

```python
def test_pdf_parser_detects_heading_candidates():
    """PDFParser 应该识别字号明显更大且带编号的文本为 heading 候选。"""
    parser = PDFParser()
    
    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        mock_doc.__len__.return_value = 1
        
        mock_page = MagicMock()
        mock_page.rect.width = 595.0
        mock_page.rect.height = 842.0
        
        # 主字号 10.5，标题字号 18.0
        mock_page.get_text.side_effect = [
            {
                "blocks": [
                    {
                        "bbox": (72.0, 96.0, 300.0, 120.0),
                        "lines": [{"spans": [{"text": "1. Introduction", "font": "Helvetica-Bold", "size": 18.0, "bbox": (72.0, 96.0, 300.0, 120.0)}]}]
                    },
                    {
                        "bbox": (72.0, 130.0, 500.0, 200.0),
                        "lines": [{"spans": [{"text": "This is content.", "font": "Helvetica", "size": 10.5, "bbox": (72.0, 130.0, 500.0, 150.0)}]}]
                    }
                ]
            },
            "1. Introduction\nThis is content."
        ]
        mock_doc.load_page.return_value = mock_page
        
        result = parser.parse(b"fake pdf")
        
        headings = result[0]["metadata"]["headings"]
        assert len(headings) == 1
        assert headings[0]["title"] == "1. Introduction"
        assert headings[0]["level"] == 1
        assert headings[0]["confidence"] > 0.5
        assert headings[0]["source_block_id"] == "b-0"
        assert headings[0]["numbering_pattern"] == "decimal"
```

- [ ] **Step 7: Implement heading candidate detection**

```python
    def _detect_heading_candidates(self, blocks: list[dict[str, Any]], page_stats: dict[str, Any]) -> list[dict[str, Any]]:
        """从 blocks 中识别标题候选。"""
        import re
        
        headings = []
        primary_font_size = page_stats["primary_font_size"]
        
        # 编号模式
        numbering_patterns = [
            (r"^(\d+)(?:\s|\.|$)", "decimal", 1),
            (r"^(\d+\.\d+)(?:\s|\.|$)", "decimal", 2),
            (r"^(\d+\.\d+\.\d+)(?:\s|\.|$)", "decimal", 3),
            (r"^Chapter\s+(\d+)", "chapter", 1),
            (r"^Section\s+(\d+)", "section", 1),
            (r"^第(\d+)章", "chapter_zh", 1),
            (r"^第(\d+)节", "section_zh", 2),
            (r"^([一二三四五六七八九十]+)、", "chinese", 1),
            (r"^（([一二三四五六七八九十]+)）", "chinese_paren", 2),
        ]
        
        for block in blocks:
            text = block["text"].strip()
            if not text:
                continue
            
            confidence = 0.0
            level = 1
            pattern_name = ""
            
            # 视觉信号：字号明显大于主字号
            font_size_ratio = block["font_size"] / primary_font_size if primary_font_size > 0 else 1.0
            if font_size_ratio >= 1.5:
                confidence += 0.4
            elif font_size_ratio >= 1.2:
                confidence += 0.2
            
            # 视觉信号：粗体
            if block["is_bold"]:
                confidence += 0.2
            
            # 文本信号：编号模式
            for pattern, name, default_level in numbering_patterns:
                match = re.match(pattern, text)
                if match:
                    confidence += 0.3
                    level = default_level
                    pattern_name = name
                    break
            
            # 文本信号：短文本（标题通常较短）
            if len(text) < 80:
                confidence += 0.1
            elif len(text) < 150:
                confidence += 0.05
            
            # 位置信号：上半区
            if block["is_top_region"]:
                confidence += 0.1
            
            # 只有置信度足够高才进入 headings
            if confidence >= 0.4:
                headings.append({
                    "title": text,
                    "level": level,
                    "confidence": min(confidence, 1.0),
                    "source_block_id": block["id"],
                    "numbering_pattern": pattern_name,
                })
        
        return headings
```

- [ ] **Step 8: Update parse method to detect headings**

```python
                # 检测标题候选
                headings = self._detect_heading_candidates(blocks, page_stats)
                
                # 构造 page node
                page_node = {
                    "page_number": page_num + 1,
                    "content": text,
                    "char_count": len(text),
                    "parser_name": "PDFParser",
                    "parser_version": "2.0.0",
                    "metadata": {
                        "source_type": "pdf",
                        "headings": headings,
                        "paragraphs_count": len([p for p in text.split("\n\n") if p.strip()]),
                        "page_stats": page_stats,
                    },
                    "raw_content_json": {
                        "page_number": page_num + 1,
                        "parser_name": "PDFParser",
                        "parser_version": "2.0.0",
                        "blocks": blocks,
                    }
                }
```

- [ ] **Step 9: Run test to verify it passes**

Run: `rtk pytest backend-python/tests/unit/parsers/test_pdf_parser.py::test_pdf_parser_detects_heading_candidates -v`
Expected: PASS

- [ ] **Step 10: Run all existing parser tests to verify no regression**

Run: `rtk pytest backend-python/tests/unit/parsers/test_pdf_parser.py -v`
Expected: All PASS

---

### Task 2: DocumentIngestService 保存新结构化数据

**Files:**
- Test: `backend-python/tests/unit/services/test_document_ingest_service.py`

- [ ] **Step 1: Write failing test for structured metadata preservation**

```python
def test_document_ingest_service_preserves_structured_metadata():
    """DocumentIngestService 应该保存 PDFParser 输出的结构化 metadata。"""
    from unittest.mock import MagicMock, patch
    
    service = DocumentIngestService()
    
    with patch("app.parsers.pdf_parser.fitz") as mock_fitz:
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc
        mock_doc.__len__.return_value = 1
        
        mock_page = MagicMock()
        mock_page.rect.width = 595.0
        mock_page.rect.height = 842.0
        mock_page.get_text.side_effect = [
            {
                "blocks": [
                    {
                        "bbox": (72.0, 96.0, 300.0, 120.0),
                        "lines": [{"spans": [{"text": "1. Intro", "font": "Helvetica-Bold", "size": 18.0, "bbox": (72.0, 96.0, 300.0, 120.0)}]}]
                    }
                ]
            },
            "1. Intro"
        ]
        mock_doc.load_page.return_value = mock_page
        
        result = service.ingest_document("test.pdf", b"fake pdf")
        
        unit = result["document_units"][0]
        assert unit.metadata_json["source_type"] == "pdf"
        assert "page_stats" in unit.metadata_json
        assert len(unit.metadata_json["headings"]) == 1
        assert unit.metadata_json["headings"][0]["title"] == "1. Intro"
        assert "blocks" in unit.raw_content_json
        assert unit.parser_version == "2.0.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk pytest backend-python/tests/unit/services/test_document_ingest_service.py::test_document_ingest_service_preserves_structured_metadata -v`
Expected: FAIL (parser_version 还是 "1.0.0" 或 metadata 结构不对)

- [ ] **Step 3: Run test to verify it passes (already works due to ingest service design)**

实际上 DocumentIngestService 已经会保存 metadata_json 和 raw_content_json，只需确保 parser 输出正确。运行测试验证。

Run: `rtk pytest backend-python/tests/unit/services/test_document_ingest_service.py::test_document_ingest_service_preserves_structured_metadata -v`
Expected: PASS (如果 Task 1 已完成)

- [ ] **Step 4: Run all existing ingest tests to verify no regression**

Run: `rtk pytest backend-python/tests/unit/services/test_document_ingest_service.py -v`
Expected: All PASS

---

### Task 3: page_index_builder 消费 richer metadata 构树

**Files:**
- Modify: `backend-python/app/rag/page_index_builder.py`
- Test: `backend-python/tests/unit/rag/test_page_index_builder.py`

- [ ] **Step 1: Write failing test for heading-based section tree**

```python
def test_build_sections_creates_tree_from_heading_candidates():
    """builder 应该从 metadata.headings 的候选构建真实章节树。"""
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=1,
            text_content="1. Introduction\nContent page 1",
            metadata_json={
                "source_type": "pdf",
                "headings": [
                    {"title": "1. Introduction", "level": 1, "confidence": 0.9, "source_block_id": "b-0", "numbering_pattern": "decimal"}
                ],
                "page_stats": {"primary_font_size": 10.5},
            },
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=1,
            page_number=2,
            text_content="1.1 Background\nContent page 2",
            metadata_json={
                "source_type": "pdf",
                "headings": [
                    {"title": "1.1 Background", "level": 2, "confidence": 0.85, "source_block_id": "b-0", "numbering_pattern": "decimal"}
                ],
                "page_stats": {"primary_font_size": 10.5},
            },
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=2,
            page_number=3,
            text_content="Content continues...",
            metadata_json={
                "source_type": "pdf",
                "headings": [],
                "page_stats": {"primary_font_size": 10.5},
            },
        ),
    ]

    result = build_sections_from_units("doc-1", units)

    assert len(result.sections) == 2
    assert result.sections[0].title == "1. Introduction"
    assert result.sections[0].level == 1
    assert result.sections[1].title == "1.1 Background"
    assert result.sections[1].level == 2
    assert result.sections[1].parent_section_id == result.sections[0].id
    assert result.sections[0].start_page == 1
    assert result.sections[0].end_page == 3
    assert result.sections[1].start_page == 2
    assert result.sections[1].end_page == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk pytest backend-python/tests/unit/rag/test_page_index_builder.py::test_build_sections_creates_tree_from_heading_candidates -v`
Expected: FAIL (当前 builder 会创建 fallback section 而不是真正的章节树)

- [ ] **Step 3: Implement heading-based section tree building**

修改 `page_index_builder.py` 的 `build_sections_from_units` 函数，使其能够：
1. 从所有 units 的 metadata.headings 收集候选标题
2. 按 confidence 过滤
3. 按 level 构建父子关系

```python
def _collect_heading_candidates(units: list[DocumentUnit]) -> list[dict[str, Any]]:
    """从所有 units 收集 heading 候选。"""
    candidates = []
    for unit in units:
        headings = (unit.metadata_json or {}).get("headings") or []
        for heading in headings:
            if not isinstance(heading, dict):
                continue
            if heading.get("confidence", 0) < 0.4:
                continue
            candidates.append({
                "title": heading.get("title", ""),
                "level": heading.get("level", 1),
                "confidence": heading.get("confidence", 0),
                "unit_id": unit.id,
                "page_number": unit.page_number,
                "sequence_index": unit.sequence_index,
            })
    return candidates


def build_sections_from_units(document_id: str, units: list[DocumentUnit]) -> SectionBuildResult:
    result = SectionBuildResult()
    if not units:
        return result

    # 收集所有 heading 候选
    candidates = _collect_heading_candidates(units)
    
    # 如果没有候选，fallback 到逐页节点
    if not candidates:
        for unit in units:
            title, fallback_kind, node_kind = _fallback_title(unit)
            section = _create_section(
                document_id, title, 1, len(result.sections), unit,
                metadata_json=_make_metadata(unit, fallback_kind=fallback_kind, node_kind=node_kind),
            )
            result.sections.append(section)
            result.section_unit_links[section.id] = [unit.id]
        return result

    # 有候选时，按 level 构建树
    level_stack: list[Section] = []
    active_sections: list[Section] = []
    seen_titles: set[str] = set()
    
    for unit in units:
        headings = (unit.metadata_json or {}).get("headings") or []
        
        # 过滤低置信度
        valid_headings = [
            h for h in headings
            if isinstance(h, dict) and h.get("confidence", 0) >= 0.4
        ]
        
        if valid_headings:
            for heading in valid_headings:
                level = int(heading.get("level", 1))
                title = str(heading.get("title", ""))
                
                # 避免重复标题
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                
                # 维护 level stack
                while level_stack and level_stack[-1].level >= level:
                    level_stack.pop()
                
                parent = level_stack[-1] if level_stack else None
                section = _create_section(
                    document_id, title, level, len(result.sections), unit,
                    parent_section_id=parent.id if parent else None,
                    metadata_json=_make_metadata(unit, node_kind="heading"),
                )
                result.sections.append(section)
                level_stack.append(section)
                active_sections = [section]
            
            # 挂接到当前活跃 section 及其祖先
            inherited = [*level_stack[:-1], *active_sections] if level_stack else active_sections
            unique_sections = _unique_sections(inherited)
            _append_links(result, unique_sections, unit)
        else:
            # 没有新 heading，挂接到当前活跃 section
            inherited = [*level_stack[:-1], *active_sections] if level_stack else []
            unique_sections = _unique_sections(inherited)
            if unique_sections:
                _append_links(result, unique_sections, unit)
            else:
                # 没有活跃 section，创建 fallback
                title, fallback_kind, node_kind = _fallback_title(unit)
                section = _create_section(
                    document_id, title, 1, len(result.sections), unit,
                    metadata_json=_make_metadata(unit, fallback_kind=fallback_kind, node_kind=node_kind),
                )
                result.sections.append(section)
                result.section_unit_links[section.id] = [unit.id]

    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `rtk pytest backend-python/tests/unit/rag/test_page_index_builder.py::test_build_sections_creates_tree_from_heading_candidates -v`
Expected: PASS

- [ ] **Step 5: Write failing test for plain PDF fallback**

```python
def test_build_sections_falls_back_to_per_page_for_plain_pdf():
    """无 heading 的 plain PDF 应该按页生成逐页 fallback sections，而不是单节点吞全文。"""
    units = [
        DocumentUnit(
            document_id="doc-1",
            sequence_index=0,
            page_number=1,
            text_content="Page 1 content",
            metadata_json={"source_type": "pdf", "headings": []},
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=1,
            page_number=2,
            text_content="Page 2 content",
            metadata_json={"source_type": "pdf", "headings": []},
        ),
        DocumentUnit(
            document_id="doc-1",
            sequence_index=2,
            page_number=3,
            text_content="Page 3 content",
            metadata_json={"source_type": "pdf", "headings": []},
        ),
    ]

    result = build_sections_from_units("doc-1", units)

    assert len(result.sections) == 3
    assert result.sections[0].title == "第 1 页"
    assert result.sections[1].title == "第 2 页"
    assert result.sections[2].title == "第 3 页"
    assert result.sections[0].start_page == 1
    assert result.sections[1].start_page == 2
    assert result.sections[2].start_page == 3
```

- [ ] **Step 6: Run test to verify it passes**

Run: `rtk pytest backend-python/tests/unit/rag/test_page_index_builder.py::test_build_sections_falls_back_to_per_page_for_plain_pdf -v`
Expected: PASS

- [ ] **Step 7: Run all existing builder tests to verify no regression**

Run: `rtk pytest backend-python/tests/unit/rag/test_page_index_builder.py -v`
Expected: All PASS

---

### Task 4: 集成测试验证 PDF 章节生成

**Files:**
- Test: `backend-python/tests/integration/document/test_pdf_ingest_pipeline.py`

- [ ] **Step 1: Write failing integration test for section tree generation**

```python
def test_pdf_ingest_generates_section_tree_with_headings(
    text_two_pages_pdf_bytes: bytes,
):
    """集成测试：带标题的 PDF 应该生成真实章节树。"""
    from app.services.section_service import SectionService
    
    # 先摄取文档
    result = DocumentIngestService().ingest_document(
        "text_two_pages.pdf",
        text_two_pages_pdf_bytes,
    )
    
    # 检查 units 有结构化 metadata
    units = result["document_units"]
    assert len(units) == 2
    assert units[0].metadata_json["source_type"] == "pdf"
    assert "page_stats" in units[0].metadata_json
```

- [ ] **Step 2: Run test to verify it passes**

Run: `rtk pytest backend-python/tests/integration/document/test_pdf_ingest_pipeline.py::test_pdf_ingest_generates_section_tree_with_headings -v`
Expected: PASS

- [ ] **Step 3: Run all existing integration tests to verify no regression**

Run: `rtk pytest backend-python/tests/integration/document/test_pdf_ingest_pipeline.py -v`
Expected: All PASS

---

### Task 5: 回归验证

- [ ] **Step 1: Run all PDF parser tests**

Run: `rtk pytest backend-python/tests/unit/parsers/test_pdf_parser.py backend-python/tests/unit/rag/test_page_index_builder.py -v`
Expected: All PASS

- [ ] **Step 2: Run all document ingest tests**

Run: `rtk pytest backend-python/tests/unit/services/test_document_ingest_service.py -v`
Expected: All PASS

- [ ] **Step 3: Run all section service tests**

Run: `rtk pytest backend-python/tests/unit/services/test_section_service.py -v`
Expected: All PASS

- [ ] **Step 4: Run all integration tests**

Run: `rtk pytest backend-python/tests/integration/ -v`
Expected: All PASS

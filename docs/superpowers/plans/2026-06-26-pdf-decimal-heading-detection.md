# PDF 十进制标题层级识别 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 PDF parser 对十进制多级标题的层级识别，使 `1`、`1.1`、`1.1.1`、`1.1.1.1` 都能输出正确的 `level`，同时保持非十进制 fallback 规则可用。

**Architecture:** 仅修改 `backend-python/app/parsers/pdf_parser.py`。新增一个只负责十进制编号提取与层级推导的 helper，由 `_detect_heading_candidates()` 先调用该 helper，再回退到 `Chapter 1`、`第1章` 等现有规则。对外的 `metadata.headings` 协议、builder 消费方式和前端数据结构保持不变。

**Tech Stack:** Python 3.12、PyMuPDF、pytest

---

## File Structure

- Modify: `backend-python/app/parsers/pdf_parser.py`
  - 新增十进制编号提取 helper
  - 重构 `_detect_heading_candidates()` 中的十进制层级判断
- Modify: `backend-python/tests/unit/parsers/test_pdf_parser.py`
  - 增加十进制标题层级识别测试
  - 增加非十进制 fallback 回归测试
- Verify: `backend-python/tests/unit/rag/test_page_index_builder.py`
  - 确认 parser 输出的 `level` 仍被 builder 正常消费

### Task 1: 补齐 parser 层级识别测试

**Files:**
- Modify: `backend-python/tests/unit/parsers/test_pdf_parser.py`
- Verify: `backend-python/app/parsers/pdf_parser.py`

- [ ] **Step 1: 写出会失败的多级十进制标题测试**

```python
@pytest.mark.us25
@pytest.mark.parametrize(
    ("heading_text", "expected_level"),
    [
        ("1 Introduction", 1),
        ("1. Introduction", 1),
        ("1.1 Background", 2),
        ("1.1.1 Details", 3),
        ("1.1.1.1 Deep Dive", 4),
    ],
)
def test_pdf_parser_detects_decimal_heading_levels(heading_text: str, expected_level: int):
    parser = PDFParser()

    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.rect.width = 595.0
        mock_page.rect.height = 842.0
        dict_output = {
            "blocks": [
                {
                    "type": 0,
                    "bbox": (72.0, 96.0, 300.0, 120.0),
                    "lines": [{
                        "spans": [{
                            "text": heading_text,
                            "font": "Helvetica-Bold",
                            "size": 18.0,
                            "bbox": (72.0, 96.0, 300.0, 120.0),
                        }]
                    }],
                },
                {
                    "type": 0,
                    "bbox": (72.0, 130.0, 500.0, 200.0),
                    "lines": [{
                        "spans": [{
                            "text": "Body text.",
                            "font": "Helvetica",
                            "size": 10.5,
                            "bbox": (72.0, 130.0, 500.0, 150.0),
                        }]
                    }],
                },
            ]
        }
        mock_page.get_text.side_effect = [dict_output, f"{heading_text}\nBody text."]
        mock_doc.load_page.return_value = mock_page

        result = parser.parse(b"fake pdf")

    headings = result[0]["metadata"]["headings"]
    assert len(headings) == 1
    assert headings[0]["title"] == heading_text
    assert headings[0]["level"] == expected_level
    assert headings[0]["numbering_pattern"] == "decimal"
```

- [ ] **Step 2: 写一条非十进制 fallback 回归测试**

```python
@pytest.mark.us25
def test_pdf_parser_preserves_chinese_chapter_heading_level():
    parser = PDFParser()

    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.rect.width = 595.0
        mock_page.rect.height = 842.0
        dict_output = {
            "blocks": [
                {
                    "type": 0,
                    "bbox": (72.0, 96.0, 300.0, 120.0),
                    "lines": [{
                        "spans": [{
                            "text": "第1章 绪论",
                            "font": "Helvetica-Bold",
                            "size": 18.0,
                            "bbox": (72.0, 96.0, 300.0, 120.0),
                        }]
                    }],
                }
            ]
        }
        mock_page.get_text.side_effect = [dict_output, "第1章 绪论"]
        mock_doc.load_page.return_value = mock_page

        result = parser.parse(b"fake pdf")

    headings = result[0]["metadata"]["headings"]
    assert len(headings) == 1
    assert headings[0]["title"] == "第1章 绪论"
    assert headings[0]["level"] == 1
    assert headings[0]["numbering_pattern"] == "chapter_zh"
```

- [ ] **Step 3: 运行 parser 定向测试，确认当前实现先失败**

Run: `rtk pytest backend-python/tests/unit/parsers/test_pdf_parser.py -q`

Expected:
- `test_pdf_parser_detects_decimal_heading_levels` 中的 `1.1`、`1.1.1`、`1.1.1.1` 断言失败
- 现有单级标题测试仍可能通过

- [ ] **Step 4: 提交测试改动**

```bash
git add backend-python/tests/unit/parsers/test_pdf_parser.py
git commit -m "test: cover decimal pdf heading levels"
```

### Task 2: 实现十进制编号 helper 并接入标题识别

**Files:**
- Modify: `backend-python/app/parsers/pdf_parser.py`
- Test: `backend-python/tests/unit/parsers/test_pdf_parser.py`

- [ ] **Step 1: 添加十进制编号 helper**

```python
DECIMAL_HEADING_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)(?:\.(?=\s)|(?=\s)|$)")


class PDFParser:
    def _extract_decimal_heading_token(self, text: str) -> tuple[str, int] | None:
        match = DECIMAL_HEADING_PATTERN.match(text.strip())
        if not match:
            return None

        token = match.group(1)
        numbering_level = len(token.split("."))
        return token, numbering_level
```

- [ ] **Step 2: 将 `_detect_heading_candidates()` 改成先走 helper，再走 fallback**

```python
    def _detect_heading_candidates(self, blocks: list[dict[str, Any]], page_stats: dict[str, Any]) -> list[dict[str, Any]]:
        headings = []
        primary_font_size = page_stats["primary_font_size"]

        fallback_patterns = [
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
            heading_level = 1
            pattern_name = ""

            font_size_ratio = block["font_size"] / primary_font_size if primary_font_size > 0 else 1.0
            if font_size_ratio >= FONT_SIZE_RATIO_STRONG:
                confidence += 0.4
            elif font_size_ratio >= FONT_SIZE_RATIO_MEDIUM:
                confidence += 0.2

            if block["is_bold"]:
                confidence += 0.2

            decimal_match = self._extract_decimal_heading_token(text)
            if decimal_match is not None:
                _, numbering_level = decimal_match
                confidence += 0.3
                heading_level = numbering_level
                pattern_name = "decimal"
            else:
                for pattern, name, default_level in fallback_patterns:
                    if re.match(pattern, text):
                        confidence += 0.3
                        heading_level = default_level
                        pattern_name = name
                        break

            if len(text) < SHORT_TEXT_THRESHOLD:
                confidence += 0.1
            elif len(text) < MEDIUM_TEXT_THRESHOLD:
                confidence += 0.05

            if block["is_top_region"]:
                confidence += 0.1

            if confidence >= HEADING_CONFIDENCE_THRESHOLD:
                headings.append({
                    "title": text,
                    "level": heading_level,
                    "confidence": min(confidence, 1.0),
                    "source_block_id": block["id"],
                    "numbering_pattern": pattern_name,
                })

        return headings
```

- [ ] **Step 3: 运行 parser 测试，确认新增用例转绿**

Run: `rtk pytest backend-python/tests/unit/parsers/test_pdf_parser.py -q`

Expected:
- 所有 parser 测试 PASS
- 新增十进制多级标题测试全部通过

- [ ] **Step 4: 提交实现改动**

```bash
git add backend-python/app/parsers/pdf_parser.py backend-python/tests/unit/parsers/test_pdf_parser.py
git commit -m "fix: detect decimal pdf heading levels"
```

### Task 3: 验证章节树构建链路未回归

**Files:**
- Verify: `backend-python/tests/unit/rag/test_page_index_builder.py`
- Verify: `backend-python/tests/unit/parsers/test_pdf_parser.py`

- [ ] **Step 1: 运行 builder 与 parser 相关回归测试**

Run: `rtk pytest backend-python/tests/unit/parsers/test_pdf_parser.py backend-python/tests/unit/rag/test_page_index_builder.py -q`

Expected:
- PASS
- `test_build_sections_creates_tree_from_heading_candidates` 继续通过，证明 builder 仍能消费修复后的 `level`

- [ ] **Step 2: 若回归失败，仅做最小修正，不改变协议**

```python
# 允许修改的方向仅限 parser 内部输出值修正，例如：
headings.append({
    "title": text,
    "level": heading_level,
    "confidence": min(confidence, 1.0),
    "source_block_id": block["id"],
    "numbering_pattern": pattern_name,
})
```

- [ ] **Step 3: 重新运行回归测试确认全绿**

Run: `rtk pytest backend-python/tests/unit/parsers/test_pdf_parser.py backend-python/tests/unit/rag/test_page_index_builder.py -q`

Expected:
- PASS

- [ ] **Step 4: 提交最终验证结果**

```bash
git add backend-python/app/parsers/pdf_parser.py backend-python/tests/unit/parsers/test_pdf_parser.py
git commit -m "test: verify pdf heading tree compatibility"
```

## Self-Review

- Spec coverage: 已覆盖 helper、新的层级变量语义、`_detect_heading_candidates()` 落位、parser 测试、builder 回归验证。
- Placeholder scan: 计划中没有 `TODO`、`TBD` 或“后续补充”类占位。
- Type consistency: helper 返回 `tuple[str, int] | None`，调用方使用 `heading_level` 作为最终 `level`，与 spec 一致。

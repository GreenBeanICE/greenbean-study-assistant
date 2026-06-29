# Section Anchored Raw Jump Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让文档原文面板按 `section` 跳转，并让 Word 文档按标题/段落切成多个 `DocumentUnit`。

**Architecture:** 后端统一把 `section` 的原文返回升级为“锚点 + units”，并让 Word 解析直接产出多 `unit` 的统一结构。前端不再猜测 `section -> unit`，而是消费后端返回的 `anchor_unit_id` 并驱动 `RawTextPanel` 自动滚动。

**Tech Stack:** FastAPI, Pydantic v2, python-docx, React 19, TypeScript, Vitest, pytest

---

### Task 1: 后端 section 锚点响应

**Files:**
- Modify: `backend-python/app/services/section_service.py`
- Modify: `backend-python/app/schemas/section_schema.py`
- Modify: `backend-python/app/api/section_controller.py`
- Test: `backend-python/tests/unit/services/test_section_service.py`
- Test: `backend-python/tests/integration/api/test_section_controller.py`

- [ ] 先写失败测试，断言 section content 返回 `anchor_unit_id` 与有序 `units`
- [ ] 运行定向 pytest，确认因响应契约缺失而失败
- [ ] 最小实现 `anchor_unit_id = 第一个关联 unit`
- [ ] 再跑定向 pytest，确认通过

### Task 2: Word 多 unit 解析与摄取

**Files:**
- Modify: `backend-python/app/parsers/word_parser.py`
- Modify: `backend-python/app/services/document_ingest_service.py`
- Test: `backend-python/tests/unit/parsers/test_word_parser.py`
- Test: `backend-python/tests/unit/services/test_document_ingest_service.py`

- [ ] 先写失败测试，断言标题段/正文段/表格分别生成多个 page-index 节点
- [ ] 运行定向 pytest，确认当前单 unit 行为导致失败
- [ ] 最小实现 Word 多节点解析与 `page_count` 语义修正
- [ ] 再跑定向 pytest，确认通过

### Task 3: 前端按 section 锚点滚动原文

**Files:**
- Modify: `src/features/section/api/sectionApi.ts`
- Modify: `src/features/workspace/type.ts`
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`
- Modify: `src/features/workspace/components/center/DocumentViewer.tsx`
- Modify: `src/features/workspace/components/center/RawTextPanel.tsx`
- Modify: `src/types/section.ts`
- Test: `src/features/section/api/sectionApi.test.ts`
- Test: `src/features/workspace/components/center/RawTextPanel.test.tsx`
- Test: `src/features/workspace/components/center/DocumentViewer.test.tsx`
- Test: `src/features/workspace/pages/WorkspacePage.test.tsx`

- [ ] 先写失败测试，断言 API 归一化、`RawTextPanel` 自动滚动、`DocumentViewer` 透传锚点、`WorkspacePage` 保存锚点
- [ ] 运行定向 vitest，确认失败原因正确
- [ ] 最小实现锚点状态流转与自动滚动
- [ ] 再跑定向 vitest，确认通过

### Task 4: 回归验证

**Files:**
- Modify: 无
- Test: `backend-python/tests/unit/parsers/test_word_parser.py`
- Test: `backend-python/tests/unit/services/test_document_ingest_service.py`
- Test: `backend-python/tests/unit/services/test_section_service.py`
- Test: `backend-python/tests/integration/api/test_section_controller.py`
- Test: `src/features/section/api/sectionApi.test.ts`
- Test: `src/features/workspace/components/center/RawTextPanel.test.tsx`
- Test: `src/features/workspace/components/center/DocumentViewer.test.tsx`
- Test: `src/features/workspace/pages/WorkspacePage.test.tsx`

- [ ] 跑后端定向 pytest 集
- [ ] 跑前端定向 vitest 集
- [ ] 确认没有新的契约断裂后结束本轮实现

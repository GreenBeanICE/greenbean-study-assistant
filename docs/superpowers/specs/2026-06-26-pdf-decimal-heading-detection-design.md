# PDF 十进制标题层级识别设计

## 背景

当前 `backend-python/app/parsers/pdf_parser.py` 通过一组按顺序匹配的正则识别标题编号层级。该实现对 `1.1 Background`、`1.1.1 Details` 这类多级十进制标题不稳，因为较宽泛的一级规则可能先命中，导致后续更具体的层级规则失效，最终生成错误的章节树。

本次设计只解决 PDF 标题中的十进制编号层级识别问题，并保持现有 PageIndex builder、章节树消费协议和置信度打分框架不变。

## 目标

- 正确识别十进制标题的层级，支持任意深度的 `1`、`1.1`、`1.1.1`、`1.1.1.1`。
- 将 `1. Introduction` 识别为一级标题。
- 保持 `Chapter 1`、`Section 1`、`第1章`、`第1节` 等非十进制规则继续可用。
- 将改动限制在 parser 内部，避免扩大协议与调用链变更面。

## 非目标

- 不在本次支持 `一、`、`（1）`、`A.`、`I.` 等非十进制编号风格。
- 不重做标题置信度模型。
- 不修改 `backend-python/app/rag/page_index_builder.py` 的输入输出结构。
- 不新增前后端字段。

## 方案概述

在 `backend-python/app/parsers/pdf_parser.py` 中新增一个十进制编号提取 helper。该 helper 只负责识别文本开头是否存在十进制章节编号，并返回：

- `token`：完整编号 token，例如 `1`、`1.1`、`1.1.1`
- `numbering_level`：由 token 分段数推导出的层级，例如 `1.1.1 -> 3`

`_detect_heading_candidates()` 不再依赖“一级/二级/三级”多条十进制正则的匹配顺序来决定层级，而是：

1. 先调用十进制 helper。
2. 若命中，则得到 `token` 和 `numbering_level`。
3. 将 `heading_level = numbering_level`，并设置 `pattern_name = "decimal"`。
4. 若未命中，再走现有非十进制 fallback 规则。

## 详细设计

### 1. 十进制编号 helper

新增一个内部 helper，例如 `_extract_decimal_heading_token(text: str)`。

职责：

- 只处理十进制编号。
- 只检查文本开头。
- 不参与置信度计算。
- 不处理非十进制编号风格。

输入示例与期望输出：

- `1 Introduction` -> `("1", 1)`
- `1. Introduction` -> `("1", 1)`
- `1.1 Background` -> `("1.1", 2)`
- `1.1.1 Details` -> `("1.1.1", 3)`
- `1.1.1.1 Deep Dive` -> `("1.1.1.1", 4)`

提取原则：

- 只接受开头为阿拉伯数字的编号。
- 允许编号主体为 `数字` 或 `数字.数字.数字...`。
- 允许编号后跟常见分隔形式，例如空格或结尾点号后接空格。
- `1. Introduction` 中末尾的点号视为编号结束分隔符，不视为第二层。

### 2. 中间层级变量

为避免“解析出来的层级”和“最终采用的层级”混用，保留两个语义明确的变量：

- `numbering_level`：仅表示十进制编号解析得到的层级。
- `heading_level`：最终写入 heading 的层级。

使用方式：

- 命中十进制 helper 时，`heading_level = numbering_level`。
- 未命中十进制 helper 时，再由 `Chapter 1`、`Section 1`、`第1章`、`第1节` 等 fallback 规则直接赋值给 `heading_level`。

这样能保证后续若扩展更多编号体系时，不需要推翻现有变量语义。

### 3. `_detect_heading_candidates()` 中的落位

保留当前整体流程：

- 视觉信号打分
- 文本信号打分
- 置信度阈值过滤

仅替换十进制编号层级判断部分：

- 十进制层级由 helper 统一提供。
- 非十进制层级继续由现有 fallback 规则提供。
- 输出结构保持：
  - `title`
  - `level`
  - `confidence`
  - `source_block_id`
  - `numbering_pattern`

因此 `page_index_builder`、`section_service` 和前端章节树消费逻辑均无需调整。

## 兼容性与风险控制

- 现有 `metadata.headings` 结构不变。
- 现有 builder 继续只消费 `level` 数值，不感知 parser 内部实现变化。
- 非十进制规则保留，避免本次修复影响 `第1章` 等已有场景。
- 本次不引入新的输出字段，避免历史数据与接口契约震荡。

已知边界：

- `一、`、`（1）`、`A.`、`I.` 仍不属于本次处理范围。
- 某些数字开头但并非标题的短文本，仍主要依赖现有视觉信号和置信度阈值进行抑制；本次不单独设计新的误判过滤器。

## 测试方案

至少补充 `backend-python/tests/unit/parsers/test_pdf_parser.py` 的 parser 单元测试，覆盖：

- `1 Introduction` -> `level = 1`
- `1. Introduction` -> `level = 1`
- `1.1 Background` -> `level = 2`
- `1.1.1 Details` -> `level = 3`
- `1.1.1.1 Deep Dive` -> `level = 4`
- `第1章 绪论` -> `level = 1`，确认 fallback 未回归

同时要求现有 `backend-python/tests/unit/rag/test_page_index_builder.py` 中依赖 `level` 构树的测试继续通过，以验证 parser 输出层级修复后，章节树构建链路仍然兼容。

## 验收标准

- parser 能正确输出多级十进制标题的 `level`。
- `1. Introduction` 被识别为一级标题。
- 非十进制 fallback 标题规则保持可用。
- 现有 builder 和 section tree 相关测试不需要修改协议即可继续通过。

## 实施范围

- 修改文件：`backend-python/app/parsers/pdf_parser.py`
- 修改测试：`backend-python/tests/unit/parsers/test_pdf_parser.py`
- 验证回归：`backend-python/tests/unit/rag/test_page_index_builder.py`

## 备注

按仓库当前协作规则，本次先写 spec，不自动创建 commit。待你确认 spec 后，再进入实现计划阶段。

# 课程文档上传与 PageIndex 结构化解析 — 技术文档

> **版本**: 1.3  
> **最后更新**: 2026-06-13  
> **适用范围**: Greenbean Study Assistant 后端 Python 服务

---

## 1. 概述

本文档描述 Greenbean Study Assistant 的**课程文档上传**与 **PageIndex 结构化解析**模块的架构设计、核心流程和技术实现细节。

### 1.1 功能目标

- 支持学生上传课程资料（PDF、Word、PPT、纯文本、Markdown、图片）
- 自动解析文档内容并提取结构化文本
- 生成统一的 **PageIndex**（页面索引）数据结构
- 为后续的 RAG 检索、AI 分析提供标准化的输入

### 1.2 支持的文件格式

| 格式 | 扩展名 | 解析器 | 说明 |
|------|--------|--------|------|
| PDF | `.pdf` | `PDFParser` | 基于 PyMuPDF，支持文本提取 |
| Word | `.docx` | `WordParser` | 基于 python-docx，支持段落/表格/标题 |
| PowerPoint | `.pptx` | `PptParser` | 基于 python-pptx，逐页提取文本与标题 |
| 纯文本 | `.txt` | `TextParser` | 支持 UTF-8/GBK 编码 |
| Markdown | `.md` | `TextParser` | 支持标题层级提取 |
| JPEG | `.jpg`, `.jpeg` | `ImageOCRParser` | 基于 Tesseract OCR，支持中/英/法 |
| PNG | `.png` | `ImageOCRParser` | 同上 |
| WebP | `.webp` | `ImageOCRParser` | 同上 |

### 1.3 暂不支持

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| 旧版 PowerPoint | `.ppt` | 97-2003 格式，提示用户转换为 .pptx |

---

## 2. 系统架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────┐
│                  API 层                          │
│         document_controller.py                   │
│     POST /api/documents/upload                   │
├─────────────────────────────────────────────────┤
│                  Service 层                      │
│         document_ingest_service.py               │
├─────────────────────────────────────────────────┤
│               Parser 层                          │
│   ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│   │PDFParser │  │WordParser│  │ImageOCRParser│  │
│   └──────────┘  └──────────┘  └──────────────┘  │
│   ┌──────────┐  ┌──────────┐                     │
│   │TextParser│  │PptParser │  ← 新增 .pptx      │
│   └──────────┘  └──────────┘                     │
│         │              │              │          │
│         │              │       ┌──────────────┐  │
│         │              │       │ImagePrepro-  │  │
│         │              │       │cessor        │  │
│         │              │       └──────────────┘  │
│   ┌──────────────────────────────────────────┐   │
│   │          ParserFactory                    │   │
│   └──────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│              工具层                               │
│   ┌──────────┐  ┌──────────┐                     │
│   │file_utils│  │text_utils│                     │
│   └──────────┘  └──────────┘                     │
└─────────────────────────────────────────────────┘
```

### 2.2 核心数据流

```
用户上传文件
    │
    ▼
[1] document_controller.upload_document()
    │  ├─ 校验文件名是否为空
    │  ├─ 校验文件格式是否支持 (is_supported)
    │  └─ 读取文件二进制流
    │
    ▼
    [2] document_ingest_service.ingest_document()
    │  ├─ ParserFactory.get_parser(filename)
    │  │   └─ 根据扩展名返回对应解析器实例
    │  └─ parser.parse(file_content)
    │      └─ 返回 List[PageIndex]（含 parser_name/parser_version/metadata）
    │
    ▼
[3] 实体化（纯内存）
    │  ├─ PageIndex[] → DocumentRecord（标题、页码、hash 等）
    │  ├─ PageIndex[𝑖] → DocumentUnit（文本、页码、偏移、追溯信息）
    │  └─ source_type → DocumentFileType 映射
    │
    ▼
[4] 返回统一响应格式 + Pydantic 实体
    {
        "filename": "xxx.pdf",
        "total_pages": 1,
        "status": "parsed_successfully",
        "page_index_preview": [PageIndex, ...],
        "document_record": DocumentRecord,
        "document_units": [DocumentUnit, ...]
    }
```

---

## 3. 核心模块详解

### 3.1 API 层 — `document_controller.py`

**路由**: `POST /api/documents/upload`

**请求格式**: `multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | UploadFile | 是 | 上传的文件 |

**响应格式**:

```json
{
    "code": 200,
    "message": "文件上传并解析成功",
    "data": {
        "filename": "notes.pdf",
        "total_pages": 3,
        "status": "parsed_successfully",
        "page_index_preview": [
            {
                "page_number": 1,
                "content": "第1页内容...",
                "char_count": 1234,
                "source_type": "pdf",
                "metadata": {
                    "headings": [{"level": 1, "text": "第一章"}],
                    "paragraphs_count": 10,
                    "tables_count": 2
                }
            }
        ]
    }
}
```

**错误响应**:

| HTTP 状态码 | 说明 |
|-------------|------|
| 400 | 文件格式不支持 / 文件内容为空 / 业务异常 |
| 422 | 请求参数校验失败（如空文件名） |
| 500 | 服务器内部错误 |

### 3.2 Service 层 — `document_ingest_service.py`

核心方法:

```python
async def ingest_document(
    filename: str,
    file_content: bytes,
    *,
    workspace_id: str | None = None,
    title: str | None = None,
    file_path: str | None = None,
    file_hash: str | None = None,
) -> dict:
    """
    文档摄取入口 — 解析 + 实体化（纯内存，不涉及 DB 持久化）

    Args:
        filename: 文件名（用于判断格式）
        file_content: 文件二进制内容
        workspace_id: 工作区 ID（可选，写入 DocumentRecord）
        title: 文档标题（可选，默认从文件名推导）
        file_path: 文件存储路径（可选）
        file_hash: 文件 SHA-256 哈希（可选）

    Returns:
        {
            "filename": str,
            "total_pages": int,
            "status": str,
            "page_index_preview": List[dict],
            "document_record": DocumentRecord,
            "document_units": List[DocumentUnit],
        }

    Raises:
        ValueError: 不支持的文件格式
    """

    # 流水线步骤:
    # Step 1 — 解析: ParserFactory → parser.parse()
    # Step 2 — 构建实体: PageIndex[] → DocumentRecord + DocumentUnit[]
    # Step 3 — 返回: 预览 + 实体（供 Controller 层事务持久化）
```

### 3.3 Parser 工厂 — `parser_factory.py`

```python
class ParserFactory:
    @staticmethod
    def get_parser(filename: str) -> BaseParser:
        """
        根据文件名返回对应的解析器实例
        
        Returns:
            PDFParser | WordParser | PptParser | TextParser | ImageOCRParser
            
        Raises:
            ValueError: 不支持的文件格式
        """
```

**路由规则**:

| 扩展名 | 解析器 |
|--------|--------|
| `.pdf` | `PDFParser` |
| `.docx` | `WordParser` |
| `.pptx` | `PptParser` |
| `.txt`, `.md` | `TextParser` |
| `.jpg`, `.jpeg`, `.png`, `.webp` | `ImageOCRParser` |
| `.ppt` | `ValueError`（提示转换） |
| 其他 | `ValueError` |

### 3.4 PDF 解析器 — `pdf_parser.py`

- 基于 **PyMuPDF (fitz)**
- 逐页提取文本
- 每页生成一个 PageIndex

### 3.5 Word 解析器 — `word_parser.py`

- 基于 **python-docx**
- 提取段落文本
- 提取表格文本（单元格拼接）
- 识别标题层级（Heading 1/2/3...）
- 所有内容合并为一个 PageIndex

### 3.6 PPT 解析器 — `ppt_parser.py`（新增）

- 基于 **python-pptx**
- 逐张幻灯片提取文本
- 识别标题占位符（placeholder idx=0）
- 每张幻灯片生成一个 PageIndex
- 支持统计 shapes 数量和段落数

### 3.7 纯文本解析器 — `text_parser.py`

- 支持 `.txt` 和 `.md` 格式
- 自动检测编码：UTF-8 → GBK → Latin-1 回退
- Markdown 文件自动识别标题层级
- 统计段落数
- 所有内容合并为一个 PageIndex

### 3.8 图片 OCR 解析器 — `image_ocr_parser.py`

- 基于 **Tesseract OCR**
- 支持语言: 中文 (`chi_sim`)、英文 (`eng`)、法文 (`fra`)
- 预处理流程: 灰度化 → 降噪 → 对比度增强 → 二值化 → 缩放
- 自动语言检测（通过 `text_utils.detect_language`）

### 3.9 图片预处理器 — `image_preprocessor.py`

```python
class ImagePreprocessor:
    MAX_WIDTH = 4096
    MAX_HEIGHT = 4096
    
    @staticmethod
    def preprocess(
        image: PIL.Image,
        apply_grayscale: bool = True,
        apply_binarization: bool = False,
        apply_denoise: bool = True,
        apply_contrast: bool = True,
        apply_deskew: bool = False,
    ) -> PIL.Image:
        """
        图片预处理流水线
        """
```

### 3.10 工具层

**`file_utils.py`**:

| 函数 | 说明 |
|------|------|
| `get_extension(filename)` | 获取文件扩展名（小写） |
| `is_supported(filename)` | 判断文件格式是否支持 |
| `is_image(filename)` | 判断是否为图片格式 |
| `is_document(filename)` | 判断是否为文档格式 |
| `get_mime_type(filename)` | 获取 MIME 类型 |

**`text_utils.py`**:

| 函数 | 说明 |
|------|------|
| `clean_text(text)` | 清洗文本（去空白、统一换行） |
| `truncate_text(text, max_chars)` | 截断文本 |
| `split_into_paragraphs(text)` | 分割段落 |
| `count_words(text)` | 统计单词数 |
| `contains_chinese(text)` | 检测是否含中文 |
| `contains_french(text)` | 检测是否含法语特殊字符 |
| `detect_language(text)` | 检测语言（zh/en/fr） |

---

## 4. PageIndex 数据结构

### 4.1 标准 PageIndex

```python
{
    "page_number": int,        # 页码（从1开始）
    "content": str,            # 提取的文本内容
    "char_count": int,         # 字符数
    "parser_name": str,        # 解析器类名（必填，用于追溯）
    "parser_version": str,     # 解析器版本号（必填，如 "1.0.0"）
    "metadata": {              # 元数据（必填，至少含 source_type）
        "source_type": str,    # "pdf" | "word" | "ppt" | "text" | "image"
        "headings": [          # 标题列表（Word/PPT/Markdown）
            {"level": 1, "text": "第一章"},
        ],
        "paragraphs_count": int,  # 段落数
        "tables_count": int,      # 表格数（仅Word）
        "shapes_count": int,      # 形状数（仅PPT）
        "is_markdown": bool,      # 是否为Markdown（仅TextParser）
        "language": str,          # 检测到的语言（仅 ImageOCRParser）
        "preprocessing_steps": [  # 预处理步骤（仅 ImageOCRParser）
            "grayscale",
            "denoise",
            "contrast_enhancement"
        ],
        "image_format": str,      # 图片格式（仅 ImageOCRParser）
        "image_width": int,       # 图片宽度（仅 ImageOCRParser）
        "image_height": int,      # 图片高度（仅 ImageOCRParser）
    }
}
```

### 4.2 各解析器输出差异

| 字段 | PDFParser | WordParser | PptParser | TextParser | ImageOCRParser |
|------|-----------|------------|-----------|------------|----------------|
| `page_number` | 实际页码 | 固定 1 | 幻灯片编号 | 固定 1 | 固定 1 |
| `content` | 每页文本 | 全部文本 | 每页文本 | 全部文本 | OCR 文本 |
| `char_count` | 每页字符数 | 总字符数 | 每页字符数 | 总字符数 | 总字符数 |
| `parser_name` | `"PDFParser"` | `"WordParser"` | `"PptParser"` | `"TextParser"` | `"ImageOCRParser"` |
| `parser_version` | `"1.0.0"` | `"1.0.0"` | `"1.0.0"` | `"1.0.0"` | `"1.0.0"` |
| `metadata.source_type` | `"pdf"` | `"word"` | `"ppt"` | `"text"` | `"image"` |
| `metadata.headings` | ❌ | ✅ | ✅ | ✅ (仅 Markdown) | ❌ |
| `metadata.paragraphs_count` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `metadata.tables_count` | ❌ | ✅ | ❌ | ❌ | ❌ |
| `metadata.shapes_count` | ❌ | ❌ | ✅ | ❌ | ❌ |
| `metadata.is_markdown` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `metadata.image_format` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `metadata.image_width` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `metadata.image_height` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `metadata.ocr_engine` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `metadata.ocr_lang` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `metadata.preprocessing_applied` | ❌ | ❌ | ❌ | ❌ | ✅ |
| `metadata.ocr_error` | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 5. 错误处理

### 5.1 异常类型

| 异常 | 触发条件 | HTTP 状态码 |
|------|----------|-------------|
| `ValueError` | 不支持的文件格式（含旧版 .ppt） | 400 |
| `HTTPException(400)` | 文件内容为空 | 400 |
| `HTTPException(400)` | 文件名不能为空 | 422 (FastAPI 校验) |
| `Exception` | 系统未知错误 | 500 |

### 5.2 边界情况

| 场景 | 处理方式 |
|------|----------|
| 空文件 | 返回 400 "文件内容为空" |
| 超大图片 | 自动缩放到 4096x4096 以内 |
| OCR 失败 | 返回空内容，不抛出异常 |
| 空文档 | 返回空 content，char_count=0 |
| 不支持格式 | 返回 400 并列出支持的格式 |
| 旧版 .ppt | 返回 400 并提示转换为 .pptx |
| 文本编码异常 | UTF-8 → GBK → Latin-1 逐级回退 |

---

## 6. 测试

### 6.1 测试文件

| 测试文件 | 测试数 | 覆盖率 |
|----------|--------|--------|
| `tests/test_document_controller.py` | 13 | 100% |
| `tests/test_document_ingest_service.py` | 21 | 100% |
| `tests/test_file_utils.py` | 13 | 100% |
| `tests/test_text_utils.py` | 30 | 100% |
| `tests/test_image_preprocessor.py` | 17 | 100% |
| `tests/test_image_ocr_parser.py` | 8 | 100% |
| `tests/test_parser_factory.py` | 12 | 100% |
| `tests/test_text_parser.py` | 7 | 100% |
| `tests/test_ppt_parser.py` | 6 | 100% |
| `tests/test_pdf_parser.py` | 1 | 100% |
| `tests/test_word_parser.py` | 5 | 100% |

### 6.2 运行测试

```bash
# 运行全部 Python 测试
cd backend-python
pytest

# 带覆盖率
pytest --cov=app --cov-report=term-missing

# 生成 HTML 覆盖率报告
pytest --cov=app --cov-report=html:../coverage/python/html
```

---

## 7. 依赖项

| 包 | 用途 | 安装 |
|----|------|------|
| `pymupdf` | PDF 解析 | `pip install pymupdf` |
| `python-docx` | Word 解析 | `pip install python-docx` |
| `python-pptx` | PPT 解析 | `pip install python-pptx` |
| `pytesseract` | OCR 识别 | `pip install pytesseract` |
| `Pillow` | 图片处理 | `pip install Pillow` |
| `pytest-cov` | 测试覆盖率 | `pip install pytest-cov` |

**外部依赖**: Tesseract OCR 引擎（需单独安装）
- 下载: https://github.com/UB-Mannheim/tesseract/releases
- 安装语言包: English, Chinese (Simplified), French

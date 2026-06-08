# 课程文档上传与 PageIndex 结构化解析 — 调用字典

> **版本**: 1.2  
> **最后更新**: 2026-06-08  
> **用途**: 前后端数据对齐、接口联调参考

---

## 1. API 接口

### 1.1 上传文档

```
POST /api/documents/upload
Content-Type: multipart/form-data
```

**请求参数**:

| 字段 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| `file` | File | FormData | ✅ | 上传的文件 |

**成功响应 (200)**:

```json
{
    "code": 200,
    "message": "文件上传并解析成功",
    "data": {
        "filename": "string",
        "total_pages": "integer",
        "status": "string",
        "page_index_preview": [
            {
                "page_number": "integer",
                "content": "string",
                "char_count": "integer",
                "source_type": "string",
                "metadata": "object | null"
            }
        ]
    }
}
```

**错误响应**:

| 状态码 | 响应体 |
|--------|--------|
| 400 | `{"detail": "暂不支持 .ppt 格式。请转换为 .pptx 后再上传。支持的格式: ..."}` |
| 400 | `{"detail": "暂不支持 .xyz 格式。支持的格式: ..."}` |
| 400 | `{"detail": "文件内容为空"}` |
| 422 | `{"detail": [{"loc": ["body", "file"], "msg": "field required"}]}` |
| 500 | `{"detail": "文件处理失败: ..."}` |

---

## 2. 数据结构字典

### 2.1 PageIndex（页面索引）

| 字段 | 类型 | 必含 | 说明 | 示例 |
|------|------|------|------|------|
| `page_number` | `int` | ✅ | 页码，从 1 开始 | `1` |
| `content` | `str` | ✅ | 提取的文本内容 | `"第一章 绪论..."` |
| `char_count` | `int` | ✅ | 字符数（含空格） | `1234` |
| `source_type` | `str` | ✅ | 来源类型枚举 | `"pdf"` |
| `metadata` | `dict` | ❌ | 元数据（可选） | `{...}` |

### 2.2 source_type 枚举

| 值 | 说明 | 来源解析器 |
|----|------|-----------|
| `"pdf"` | PDF 文档 | `PDFParser` |
| `"word"` | Word 文档 | `WordParser` |
| `"ppt"` | PowerPoint 演示文稿 | `PptParser` |
| `"text"` | 纯文本 / Markdown | `TextParser` |
| `"image"` | 图片文件 | `ImageOCRParser` |

### 2.3 metadata 结构

#### PDF 文档

```json
{
    "source_type": "pdf"
}
```

#### Word 文档

```json
{
    "source_type": "word",
    "headings": [
        {"level": 1, "text": "第一章"},
        {"level": 2, "text": "1.1 背景"}
    ],
    "paragraphs_count": 15,
    "tables_count": 2
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `headings` | `list[dict]` | 标题列表，`level` 为标题层级（1-9），`text` 为标题文本 |
| `paragraphs_count` | `int` | 段落总数 |
| `tables_count` | `int` | 表格总数 |

#### PowerPoint 演示文稿

```json
{
    "source_type": "ppt",
    "headings": [
        {"level": 1, "text": "第一章 绪论"}
    ],
    "paragraphs_count": 5,
    "shapes_count": 3
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `headings` | `list[dict]` | 标题列表（基于占位符 idx=0 识别） |
| `paragraphs_count` | `int` | 段落总数 |
| `shapes_count` | `int` | 幻灯片中形状总数 |

#### 纯文本 / Markdown

```json
{
    "source_type": "text",
    "is_markdown": true,
    "headings": [
        {"level": 1, "text": "第一章"},
        {"level": 2, "text": "1.1 背景"}
    ],
    "paragraphs_count": 10
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `is_markdown` | `bool` | 是否为 Markdown 格式 |
| `headings` | `list[dict]` | 标题列表（仅 Markdown 时存在） |
| `paragraphs_count` | `int` | 段落总数 |

#### 图片文件

```json
{
    "source_type": "image",
    "language": "chi_sim",
    "preprocessing_steps": [
        "grayscale",
        "denoise",
        "contrast_enhancement"
    ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `language` | `str` | OCR 使用的语言代码 |
| `preprocessing_steps` | `list[str]` | 预处理步骤列表 |

### 2.4 language 枚举（OCR）

| 值 | 说明 |
|----|------|
| `"eng"` | 英语 |
| `"chi_sim"` | 简体中文 |
| `"fra"` | 法语 |

### 2.5 preprocessing_steps 枚举

| 值 | 说明 |
|----|------|
| `"grayscale"` | 灰度化 |
| `"denoise"` | 降噪 |
| `"contrast_enhancement"` | 对比度增强 |
| `"binarization"` | 二值化 |
| `"scaling"` | 缩放 |

### 2.6 status 枚举

| 值 | 说明 |
|----|------|
| `"parsed_successfully"` | 解析成功 |

---

## 3. 文件格式对照表

### 3.1 扩展名 → 解析器

| 扩展名 | 解析器 | source_type |
|--------|--------|-------------|
| `.pdf` | `PDFParser` | `"pdf"` |
| `.docx` | `WordParser` | `"word"` |
| `.pptx` | `PptParser` | `"ppt"` |
| `.txt` | `TextParser` | `"text"` |
| `.md` | `TextParser` | `"text"` |
| `.jpg` | `ImageOCRParser` | `"image"` |
| `.jpeg` | `ImageOCRParser` | `"image"` |
| `.png` | `ImageOCRParser` | `"image"` |
| `.webp` | `ImageOCRParser` | `"image"` |
| `.ppt` | ❌ 提示转换 | - |

### 3.2 扩展名 → MIME 类型

| 扩展名 | MIME 类型 |
|--------|-----------|
| `.pdf` | `application/pdf` |
| `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `.pptx` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `.txt` | `text/plain` |
| `.md` | `text/markdown` |
| `.jpg` | `image/jpeg` |
| `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |
| `.webp` | `image/webp` |

---

## 4. 前端调用示例

### 4.1 JavaScript / TypeScript

```typescript
// 上传文档
async function uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
    }
    
    return response.json();
}

// 使用示例
const fileInput = document.querySelector('input[type="file"]');
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    try {
        const result = await uploadDocument(file);
        console.log('解析成功:', result.data);
        
        result.data.page_index_preview.forEach(page => {
            console.log(`第 ${page.page_number} 页: ${page.char_count} 字符`);
            console.log(`来源: ${page.source_type}`);
            console.log(`内容预览: ${page.content.slice(0, 100)}...`);
        });
    } catch (err) {
        console.error('上传失败:', err.message);
    }
});
```

### 4.2 cURL

```bash
# 上传 PDF
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/document.pdf"

# 上传 PPT
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/slides.pptx"

# 上传图片
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/photo.jpg"

# 上传 Word
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/notes.docx"

# 上传纯文本
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/notes.txt"

# 上传 Markdown
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/readme.md"
```

### 4.3 Python (requests)

```python
import requests

def upload_document(file_path: str) -> dict:
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            'http://localhost:8000/api/documents/upload',
            files=files
        )
    response.raise_for_status()
    return response.json()

# 使用
result = upload_document('notes.pdf')
print(result['data']['total_pages'])
for page in result['data']['page_index_preview']:
    print(page['page_number'], page['char_count'])
```

---

## 5. 类型定义（TypeScript）

```typescript
// 上传响应
interface UploadResponse {
    code: number;
    message: string;
    data: DocumentData;
}

// 文档数据
interface DocumentData {
    filename: string;
    total_pages: number;
    status: 'parsed_successfully';
    page_index_preview: PageIndex[];
}

// 页面索引
interface PageIndex {
    page_number: number;
    content: string;
    char_count: number;
    source_type: 'pdf' | 'word' | 'ppt' | 'text' | 'image';
    metadata?: PageMetadata | null;
}

// 元数据联合类型
type PageMetadata = PdfMetadata | WordMetadata | PptMetadata | TextMetadata | ImageMetadata;

// PDF 元数据
interface PdfMetadata {
    source_type: 'pdf';
}

// Word 元数据
interface WordMetadata {
    source_type: 'word';
    headings: Heading[];
    paragraphs_count: number;
    tables_count: number;
}

// PPT 元数据
interface PptMetadata {
    source_type: 'ppt';
    headings: Heading[];
    paragraphs_count: number;
    shapes_count: number;
}

// 纯文本 / Markdown 元数据
interface TextMetadata {
    source_type: 'text';
    is_markdown: boolean;
    headings?: Heading[];
    paragraphs_count: number;
}

// 图片元数据
interface ImageMetadata {
    source_type: 'image';
    language: 'eng' | 'chi_sim' | 'fra';
    preprocessing_steps: PreprocessingStep[];
}

// 标题
interface Heading {
    level: number;  // 1-9
    text: string;
}

// 预处理步骤
type PreprocessingStep = 
    | 'grayscale'
    | 'denoise'
    | 'contrast_enhancement'
    | 'binarization'
    | 'scaling';
```

---

## 6. 错误码速查

| 状态码 | 错误场景 | 处理建议 |
|--------|----------|----------|
| 200 | 成功 | 正常解析返回 |
| 400 | 格式不支持（含旧版 .ppt） | 前端提示用户更换格式或转换 |
| 400 | 文件为空 | 前端提示用户重新上传 |
| 422 | 参数校验失败 | 检查请求格式 |
| 500 | 服务器错误 | 联系后端排查 |

---

## 7. 版本兼容性

| 接口版本 | 变更内容 | 兼容性 |
|----------|----------|--------|
| v1.2 | 新增 `.pptx` 支持，新增 `source_type: "ppt"` | 向后兼容 |
| v1.1 | 新增 `.txt`/`.md` 支持，新增 `source_type: "text"` | 向后兼容 |
| v1 (初始) | 初始版本 | - |

---

## 8. 附录：快速参考卡片

### 请求卡片

```
POST /api/documents/upload
┌─────────────────────────┐
│ FormData:               │
│   file: File (必填)     │
└─────────────────────────┘
```

### 响应卡片

```
200 OK
┌─────────────────────────────────┐
│ code: 200                       │
│ message: "文件上传并解析成功"    │
│ data: {                         │
│   filename: string,             │
│   total_pages: int,             │
│   status: "parsed_successfully",│
│   page_index_preview: [         │
│     {                           │
│       page_number: int,         │
│       content: string,          │
│       char_count: int,          │
│       source_type: str,         │
│       metadata: object|null     │
│     }                           │
│   ]                             │
│ }                               │
└─────────────────────────────────┘
```

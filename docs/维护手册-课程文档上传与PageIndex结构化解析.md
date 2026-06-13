# 课程文档上传与 PageIndex 结构化解析 — 维护手册

> **版本**: 1.3  
> **最后更新**: 2026-06-13  
> **用途**: 运维部署、问题排查、性能调优参考

---

## 1. 部署要求

### 1.1 硬件要求

| 组件 | 最低要求 | 推荐 |
|------|----------|------|
| CPU | 2 核 | 4 核以上 |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 10 GB 可用空间 | 50 GB SSD |
| 网络 | 100 Mbps | 1 Gbps |

### 1.2 软件依赖

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | ≥ 3.10 | 推荐 3.12 |
| Tesseract OCR | ≥ 5.0 | 需安装中/英/法语言包 |
| pip | 最新版 | 包管理 |

### 1.3 Python 包依赖

```bash
# 核心依赖
pip install fastapi uvicorn
pip install pymupdf          # PDF 解析
pip install python-docx      # Word 解析
pip install python-pptx      # PPT 解析
pip install pytesseract      # OCR 识别
pip install Pillow           # 图片处理

# 测试依赖
pip install pytest pytest-cov pytest-asyncio
pip install httpx            # 异步 HTTP 测试
```

### 1.4 Tesseract OCR 安装

**Windows**:
1. 下载安装包: https://github.com/UB-Mannheim/tesseract/releases
2. 安装时勾选语言包: English, Chinese (Simplified), French
3. 添加安装目录到系统 PATH（如 `C:\Program Files\Tesseract-OCR`）
4. 验证安装: `tesseract --list-langs`

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-chi-sim tesseract-ocr-fra
```

**macOS**:
```bash
brew install tesseract
brew install tesseract-lang
```

---

## 2. 启动与运行

### 2.1 开发环境

```bash
cd backend-python
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2.2 生产环境

```bash
cd backend-python
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2.3 Docker 部署（推荐）

```dockerfile
FROM python:3.12-slim

# 安装 Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 3. 配置说明

### 3.1 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `TESSERACT_CMD` | `tesseract` | Tesseract OCR 可执行文件路径 |
| `UPLOAD_MAX_SIZE` | `50MB` | 上传文件大小限制 |
| `OCR_TIMEOUT` | `30` | OCR 超时时间（秒） |

### 3.2 Tesseract 路径配置

如果 Tesseract 不在系统 PATH 中，需要在代码中配置：

```python
import pytesseract
# Windows 示例
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

## 4. 监控与日志

### 4.1 关键日志点

| 模块 | 日志级别 | 日志内容 |
|------|----------|----------|
| `document_controller` | INFO | 文件上传请求（文件名、大小） |
| `document_controller` | ERROR | 文件处理失败（异常详情） |
| `document_ingest_service` | INFO | 解析开始/完成（文件名、页数） |
| `image_ocr_parser` | WARNING | OCR 识别失败（图片名） |
| `image_preprocessor` | DEBUG | 预处理步骤详情 |

### 4.2 性能指标

| 指标 | 正常范围 | 告警阈值 |
|------|----------|----------|
| PDF 解析时间 | < 2s/100页 | > 5s |
| Word 解析时间 | < 1s | > 3s |
| PPT 解析时间 | < 2s/50页 | > 5s |
| OCR 识别时间 | < 5s/图片 | > 15s |
| 上传文件大小 | < 10MB | > 50MB |

---

## 5. 常见问题排查

### 5.1 Tesseract OCR 相关问题

**问题**: `pytesseract.pytesseract.TesseractNotFoundError: tesseract is not installed`

**解决**:
1. 确认 Tesseract 已安装: `tesseract --version`
2. 检查 PATH 环境变量
3. 手动设置路径: `pytesseract.pytesseract.tesseract_cmd = r'C:\...\tesseract.exe'`

**问题**: `pytesseract.pytesseract.TesseractError: (1, 'Error opening data file...')`

**解决**:
1. 检查语言包是否安装: `tesseract --list-langs`
2. 设置 `TESSDATA_PREFIX` 环境变量指向 tessdata 目录

### 5.2 文件解析问题

**问题**: PDF 解析返回空内容

**可能原因**:
- PDF 是扫描件（需 OCR 处理）
- PDF 受密码保护
- PDF 编码异常

**解决**:
- 扫描件 PDF 需先经过 OCR 处理
- 检查 PDF 是否可正常打开

**问题**: Word 文档解析后 headings 为空

**可能原因**:
- 文档未使用 Word 内置标题样式
- 文档使用自定义样式

**解决**: 建议用户使用 Word 内置的 Heading 1/2/3 样式

**问题**: PPT 解析后 headings 为空

**可能原因**:
- 幻灯片未使用标题占位符
- 使用文本框代替标题占位符

**解决**: 建议用户使用 PPT 内置的标题占位符

### 5.3 编码问题

**问题**: 文本文件解析出现乱码

**解决**:
- 系统自动尝试 UTF-8 → GBK → Latin-1 回退
- 建议用户保存为 UTF-8 编码

### 5.4 性能问题

**问题**: 大文件上传超时

**解决**:
1. 检查 `UPLOAD_MAX_SIZE` 配置
2. 考虑前端分片上传
3. 增加服务器超时时间

**问题**: OCR 处理过慢

**解决**:
1. 图片预处理会自动缩放到 4096x4096 以内
2. 建议用户上传清晰、高对比度的图片
3. 考虑使用 GPU 加速的 OCR 引擎

---

## 6. 测试指南

### 6.1 运行测试

```bash
# 运行全部测试
cd backend-python
pytest

# 按 User Story 筛选运行
pytest -m us25 -v

# 运行特定测试文件
pytest tests/test_ppt_parser.py -v

# 运行特定测试类
pytest tests/test_parser_factory.py::TestParserFactory -v

# 运行特定测试方法
pytest tests/test_parser_factory.py::TestParserFactory::test_factory_returns_ppt_parser -v
```

### 6.2 覆盖率报告

```bash
# 终端覆盖率报告
pytest --cov=app --cov-report=term-missing

# HTML 覆盖率报告
pytest --cov=app --cov-report=html:../coverage/python/html
# 打开 coverage/python/html/index.html 查看
```

### 6.3 测试数据

测试文件位于 `tests/` 目录下，使用内存生成的方式创建测试数据：

- `test_ppt_parser.py`: 使用 `python-pptx` 库动态生成 `.pptx` 文件
- `test_word_parser.py`: 使用 `python-docx` 库动态生成 `.docx` 文件
- `test_pdf_parser.py`: 使用 `PyMuPDF` 库动态生成 `.pdf` 文件
- `test_image_ocr_parser.py`: 使用 `Pillow` 库动态生成测试图片

### 6.4 测试标记（Markers）

所有与课程文档上传和解析相关的测试均已添加 `@pytest.mark.us25` 标记，方便按 User Story 筛选执行：

```bash
# 仅运行 US25 相关测试
pytest -m us25 -v

# 排除 US25 测试运行其余测试
pytest -m "not us25" -v
```

涉及标记的测试文件及数量：

| 测试文件 | 标记数 |
|----------|--------|
| `test_document_controller.py` | 13 |
| `test_document_ingest_service.py` | 21 |
| `test_file_utils.py` | 13 |
| `test_text_utils.py` | 30 |
| `test_image_preprocessor.py` | 17 |
| `test_image_ocr_parser.py` | 8 |
| `test_parser_factory.py` | 12 |
| `test_text_parser.py` | 7 |
| `test_ppt_parser.py` | 6 |
| `test_pdf_parser.py` | 1 |
| `test_word_parser.py` | 5 |
| **合计** | **133** |

---

## 7. 扩展指南

### 7.1 添加新的解析器

1. 在 `app/parsers/` 下创建新的解析器文件（如 `excel_parser.py`）
2. 实现 `parse(self, file_content: bytes) -> List[Dict]` 方法
3. 在 `parser_factory.py` 中注册新格式
4. 在 `file_utils.py` 中添加扩展名支持
5. 编写对应的测试文件
6. 更新文档

### 7.2 添加新的文件格式

1. 在 `file_utils.py` 的 `SUPPORTED_EXTENSIONS` 中添加扩展名
2. 在 `parser_factory.py` 中添加路由规则
3. 在 `document_controller.py` 中更新支持格式提示
4. 更新文档

---

## 8. 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.2 | 2026-06-08 | 新增 PPT 解析器（.pptx），更新 file_utils 和 parser_factory |
| 1.1 | 2026-06-08 | 新增 TextParser（.txt/.md），更新文档 |
| 1.0 | 2026-06-08 | 初始版本，支持 PDF/Word/图片解析 |

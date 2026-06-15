"""
用 tests/pdf/test.pdf 真实 PDF 测试 parser 流水线。

运行方式:
   cd backend-python && python scripts/test_real_pdf.py
"""
import sys
from pathlib import Path

# 确保 backend-python 根目录在 sys.path 中
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.parsers.pdf_parser import PDFParser
from app.parsers.parser_factory import ParserFactory
from app.services.document_ingest_service import DocumentIngestService

# ---- 加载真实 PDF ----
PDF_PATH = ROOT.parent / "tests" / "pdf" / "test.pdf"
if not PDF_PATH.exists():
    raise FileNotFoundError(f"测试 PDF 未找到: {PDF_PATH}")

pdf_bytes = PDF_PATH.read_bytes()
print(f"✅ 加载 PDF: {PDF_PATH.name} ({len(pdf_bytes)} 字节)\n")

# ============================================================
# 1. 直接测试 PDFParser.parse()
# ============================================================
print("=" * 60)
print("第 1 层：PDFParser.parse() 直接解析")
print("=" * 60)

parser = PDFParser()
pages = parser.parse(pdf_bytes)

print(f"总页数: {len(pages)}")
all_passed = True

for page in pages:
    pn = page["page_number"]
    cnt = page["char_count"]
    content = page["content"]
    src_type = page["metadata"]["source_type"]
    parser_name = page["parser_name"]
    parser_ver = page["parser_version"]
    headings = page["metadata"]["headings"]
    para_count = page["metadata"]["paragraphs_count"]

    # 逐项校验
    checks = [
        ("page_number 为 int", isinstance(pn, int)),
        ("page_number >= 1", pn >= 1),
        ("char_count > 0", cnt > 0),
        ("char_count == len(content)", cnt == len(content)),
        ("source_type == 'pdf'", src_type == "pdf"),
        ("parser_name == 'PDFParser'", parser_name == "PDFParser"),
        ("parser_version == '1.0.0'", parser_ver == "1.0.0"),
        ("headings 为 list", isinstance(headings, list)),
        ("paragraphs_count > 0", para_count > 0),
    ]
    status_icon = "✅" if all(ok for _, ok in checks) else "❌"
    print(f"\n{status_icon} 第{pn}页:")
    print(f"    char_count = {cnt}")
    print(f"    content 前 80 字符: {content[:80]}...")
    if not all(ok for _, ok in checks):
        all_passed = False
        for desc, ok in checks:
            if not ok:
                print(f"    ❌ 失败: {desc}")

print(f"\nPDFParser 测试结果: {'✅ 全部通过' if all_passed else '❌ 存在失败项'}")

# ============================================================
# 2. 测试 ParserFactory 针对 PDF 的分发
# ============================================================
print("\n" + "=" * 60)
print("第 2 层：ParserFactory 分发 + 解析")
print("=" * 60)

factory_parser = ParserFactory.get_parser("test.pdf")
assert isinstance(factory_parser, PDFParser), "ParserFactory 应返回 PDFParser"
factory_pages = factory_parser.parse(pdf_bytes)
assert len(factory_pages) == len(pages), "工厂解析的页数应一致"
for i, p in enumerate(factory_pages):
    assert p["char_count"] == pages[i]["char_count"], f"第{i+1}页字符数应一致"
print("✅ ParserFactory 正确返回 PDFParser，解析结果与直接调用一致")

# ============================================================
# 3. 测试完整流水线 DocumentIngestService
# ============================================================
print("\n" + "=" * 60)
print("第 3 层：DocumentIngestService 完整流水线")
print("=" * 60)

service = DocumentIngestService()
result = service.ingest_document("test.pdf", pdf_bytes)

print(f"文件名: {result['filename']}")
print(f"总页数: {result['total_pages']}")
print(f"状态: {result['status']}")
print(f"DocumentUnits 数量: {len(result['document_units'])}")
print(f"\nPageIndex 预览:")
preview_ok = True
for p in result["page_index_preview"]:
    print(f"  第{p['page_number']}页: {p['char_count']} 字符, source_type={p['source_type']}")
    if p["source_type"] != "pdf":
        preview_ok = False

# 校验 DocumentRecord
record = result["document_record"]
record_checks = [
    ("original_filename == 'test.pdf'", record.original_filename == "test.pdf"),
    ("page_count == 2", record.page_count == 2),
    ("status == PARSED", record.status.value == "parsed"),
]
print(f"\nDocumentRecord 校验:")
for desc, ok in record_checks:
    print(f"  {'✅' if ok else '❌'} {desc}")
    if not ok:
        preview_ok = False

# 校验 DocumentUnits
units = result["document_units"]
unit_checks = [
    ("unit 数量 == 总页数", len(units) == 2),
    ("unit[0].page_number == 1", units[0].page_number == 1),
    ("unit[1].page_number == 2", units[1].page_number == 2),
    ("unit[0].text_content 不为空", len(units[0].text_content) > 0),
    ("unit[1].text_content 不为空", len(units[1].text_content) > 0),
    ("unit[0].parser_name == 'PDFParser'", units[0].parser_name == "PDFParser"),
]
print(f"\nDocumentUnits 校验:")
for desc, ok in unit_checks:
    print(f"  {'✅' if ok else '❌'} {desc}")
    if not ok:
        preview_ok = False

print(f"\n流水线测试结果: {'✅ 全部通过' if preview_ok else '❌ 存在失败项'}")

# ============================================================
# 汇总
# ============================================================
print("\n" + "=" * 60)
if all_passed and preview_ok:
    print("🎉 所有三层测试全部通过！PDF Parser 工作正常。")
else:
    print("❌ 部分测试未通过，请检查上方输出。")
print("=" * 60)
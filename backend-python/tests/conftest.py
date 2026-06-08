import os
import sys
import tempfile
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = Path(__file__).resolve().parent
TEST_TEMP_ROOT = TESTS_ROOT / "tmp" / "pytest" / str(os.getpid())

TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(TEST_TEMP_ROOT)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def pytest_configure(config):
    if getattr(config.option, "basetemp", None) is None:
        config.option.basetemp = str(TEST_TEMP_ROOT)
    
    # 注册 US 标记
    config.addinivalue_line("markers", "us25: 课程文档上传与 PageIndex 结构化解析")

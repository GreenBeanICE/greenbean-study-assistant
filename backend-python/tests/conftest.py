import os
import sys
import tempfile
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = Path(__file__).resolve().parent
FIXTURES_ROOT = TESTS_ROOT / "fixtures"
PDF_FIXTURES_ROOT = FIXTURES_ROOT / "pdf"
WORD_FIXTURES_ROOT = FIXTURES_ROOT / "word"
TEST_TEMP_ROOT = TESTS_ROOT / "tmp" / "pytest" / str(os.getpid())

TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(TEST_TEMP_ROOT)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def pytest_configure(config):
    if getattr(config.option, "basetemp", None) is None:
        config.option.basetemp = str(TEST_TEMP_ROOT)


def pytest_collection_modifyitems(items):
    """根据测试所在目录自动添加测试层级标记。"""
    for item in items:
        path_parts = Path(str(item.path)).parts
        if "unit" in path_parts:
            item.add_marker(pytest.mark.unit)
        elif "integration" in path_parts:
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def pdf_fixtures_dir() -> Path:
    return PDF_FIXTURES_ROOT


@pytest.fixture(scope="session")
def word_fixtures_dir() -> Path:
    return WORD_FIXTURES_ROOT


@pytest.fixture
def provider_config_factory():
    from app.entities.provider_config import ProviderConfig
    from app.enums.api_mode import ApiMode
    from app.enums.purpose import Purpose

    def make_config(
        name: str = "test-cfg",
        is_active: bool = False,
        purpose: Purpose = Purpose.CHAT,
        embedding_dimension: int | None = None,
    ) -> ProviderConfig:
        return ProviderConfig(
            name=name,
            api_mode=ApiMode.OPENAI_COMPAT,
            api_key="sk-test",
            api_host="https://api.test.com",
            model_id="test-model",
            display_name=name,
            is_active=is_active,
            purpose=purpose,
            embedding_dimension=embedding_dimension,
        )

    return make_config


@pytest.fixture(scope="session")
def text_two_pages_pdf_path(pdf_fixtures_dir: Path) -> Path:
    return pdf_fixtures_dir / "text_two_pages.pdf"


@pytest.fixture(scope="session")
def text_two_pages_pdf_bytes(text_two_pages_pdf_path: Path) -> bytes:
    return text_two_pages_pdf_path.read_bytes()

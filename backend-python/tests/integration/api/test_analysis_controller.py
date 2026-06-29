from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_analysis_service
from app.main import app


@pytest.fixture
def client():
    analysis_service = MagicMock()
    app.dependency_overrides[get_analysis_service] = lambda: analysis_service
    yield TestClient(app), analysis_service
    app.dependency_overrides.clear()


def test_get_section_analysis_returns_404_when_missing(client):
    test_client, analysis_service = client
    analysis_service.get_section_analysis.side_effect = ValueError("Section not found: sec-404")

    response = test_client.get("/api/analyses/sections/sec-1")

    assert response.status_code == 404


def test_get_section_analysis_returns_null_when_analysis_not_generated(client):
    test_client, analysis_service = client
    analysis_service.get_section_analysis.return_value = None

    response = test_client.get("/api/analyses/sections/sec-1")

    assert response.status_code == 200
    assert response.json()["data"] is None


def test_get_section_analysis_success(client):
    test_client, analysis_service = client
    from app.entities.analysis_result import AnalysisResult
    from app.enums.analysis_type import AnalysisType

    analysis_service.get_section_analysis.return_value = AnalysisResult(
        document_id="doc-1",
        section_id="sec-1",
        analysis_type=AnalysisType.SECTION,
        language="zh",
        content_markdown="## 中文总结\n\n已存在摘要",
        content_json={
            "summary": "已存在摘要",
            "key_concepts": [],
            "terms": [],
            "highlights": [],
            "source_refs": [],
        },
    )

    response = test_client.get("/api/analyses/sections/sec-1")

    assert response.status_code == 200
    assert response.json()["data"]["section_id"] == "sec-1"
    assert response.json()["data"]["content_json"]["summary"] == "已存在摘要"


def test_generate_section_analysis_success(client):
    test_client, analysis_service = client
    from app.entities.analysis_result import AnalysisResult
    from app.enums.analysis_type import AnalysisType

    analysis_service.generate_section_analysis = AsyncMock(
        return_value=AnalysisResult(
            document_id="doc-1",
            section_id="sec-1",
            analysis_type=AnalysisType.SECTION,
            language="zh",
            content_markdown="## 中文总结\n\n摘要",
            content_json={
                "summary": "摘要",
                "key_concepts": ["概念 A"],
                "terms": [],
                "highlights": ["重点 A"],
                "source_refs": [{"page": 3, "title": "1.1 背景介绍"}],
            },
            prompt_version="section-v1",
        )
    )

    response = test_client.post(
        "/api/analyses/sections/sec-1/generate",
        json={"language": "zh", "force_regenerate": False},
    )

    assert response.status_code == 200
    assert response.json()["data"]["section_id"] == "sec-1"
    assert response.json()["data"]["content_json"]["summary"] == "摘要"
    assert response.json()["data"]["source_refs"][0]["page"] == 3


def test_generate_section_analysis_returns_400_when_section_has_no_source(client):
    test_client, analysis_service = client
    analysis_service.generate_section_analysis = AsyncMock(
        side_effect=ValueError("资料依据不足：该章节当前没有可用于生成解析的原文")
    )

    response = test_client.post(
        "/api/analyses/sections/sec-empty/generate",
        json={"language": "zh", "force_regenerate": False},
    )

    assert response.status_code == 400
    assert "资料依据不足" in response.json()["detail"]


def test_generate_section_analysis_returns_404_when_section_missing(client):
    test_client, analysis_service = client
    analysis_service.generate_section_analysis = AsyncMock(
        side_effect=ValueError("Section not found: sec-404")
    )

    response = test_client.post(
        "/api/analyses/sections/sec-404/generate",
        json={"language": "zh", "force_regenerate": False},
    )

    assert response.status_code == 404

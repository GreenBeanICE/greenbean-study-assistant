"""小节分析 API contract 测试。"""

import pytest
from fastapi.testclient import TestClient
import sqlite3

from app.entities.analysis_result import AnalysisResult
from app.enums.analysis_type import AnalysisType
from app.main import app
from app.providers.base import ChatResult, ProviderConfigurationError
from app.providers.registry import ProviderNotFoundError
from app.rag.context_builder import SectionNotFoundError, SectionPageRangeMissingError


class FakeSectionAnalysisService:
    def __init__(self, result: AnalysisResult | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls: list[dict] = []

    async def analyze_section(
        self,
        *,
        section_id: str,
        language: str,
        model_name: str | None,
        prompt_version: str,
    ) -> AnalysisResult:
        self.calls.append(
            {
                "section_id": section_id,
                "language": language,
                "model_name": model_name,
                "prompt_version": prompt_version,
            }
        )
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def traceable_analysis_result() -> AnalysisResult:
    return AnalysisResult(
        id="analysis-1",
        document_id="doc-1",
        section_id="sec-1",
        analysis_type=AnalysisType.SECTION,
        language="zh",
        content_markdown="人工智能正在改变教育资料的学习方式。",
        content_json={
            "section_id": "sec-1",
            "section_title": "1.1 背景介绍",
            "status": "completed",
            "sentences": [
                {
                    "id": "s1",
                    "text": "人工智能正在改变教育资料的学习方式。",
                    "citations": [
                        {
                            "id": "c1",
                            "page": 1,
                            "document_unit_id": "unit-1",
                            "chunk_id": "chunk-1",
                            "source_text": "人工智能技术取得了飞速发展",
                            "start_char": 3,
                            "end_char": 17,
                        }
                    ],
                }
            ],
            "source_pages": [
                {
                    "page": 1,
                    "document_unit_id": "unit-1",
                    "text": "近年来，人工智能技术取得了飞速发展。",
                }
            ],
        },
        model_name="gemini-2.5-flash",
        prompt_version="section-analysis-v1",
    )


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


def override_analysis_service(fake_service: FakeSectionAnalysisService):
    from app.api.analysis_controller import get_section_analysis_service

    app.dependency_overrides[get_section_analysis_service] = lambda: fake_service


def test_analyze_section_returns_sentence_level_citations(client):
    fake_service = FakeSectionAnalysisService(result=traceable_analysis_result())
    override_analysis_service(fake_service)

    response = client.post(
        "/api/analysis/sections/sec-1",
        json={
            "language": "zh",
            "model_name": "gemini-2.5-flash",
            "prompt_version": "section-analysis-v1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["message"] == "小节分析完成"
    assert body["data"]["section_id"] == "sec-1"
    assert body["data"]["analysis_type"] == "section"
    assert body["data"]["content_json"]["status"] == "completed"
    assert body["data"]["content_json"]["sentences"][0]["citations"][0]["document_unit_id"] == "unit-1"
    assert body["data"]["content_json"]["source_pages"][0]["text"] == "近年来，人工智能技术取得了飞速发展。"
    assert fake_service.calls == [
        {
            "section_id": "sec-1",
            "language": "zh",
            "model_name": "gemini-2.5-flash",
            "prompt_version": "section-analysis-v1",
        }
    ]


def test_analyze_section_returns_404_when_section_missing(client):
    fake_service = FakeSectionAnalysisService(error=SectionNotFoundError("Section not found: missing"))
    override_analysis_service(fake_service)

    response = client.post("/api/analysis/sections/missing", json={"language": "zh"})

    assert response.status_code == 404
    assert "Section not found" in response.json()["detail"]


def test_analyze_section_returns_400_when_page_range_missing(client):
    fake_service = FakeSectionAnalysisService(
        error=SectionPageRangeMissingError("Section page range is missing or invalid: sec-1")
    )
    override_analysis_service(fake_service)

    response = client.post("/api/analysis/sections/sec-1", json={"language": "zh"})

    assert response.status_code == 400
    assert "page range" in response.json()["detail"]


def test_analyze_section_returns_503_when_provider_not_configured(client):
    fake_service = FakeSectionAnalysisService(
        error=ProviderNotFoundError("当前没有激活的 provider，请先配置并激活。")
    )
    override_analysis_service(fake_service)

    response = client.post("/api/analysis/sections/sec-1", json={"language": "zh"})

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "AI_PROVIDER_NOT_CONFIGURED",
        "message": "尚未配置 AI 模型服务",
    }


def test_analyze_section_returns_503_when_provider_secret_invalid(client):
    fake_service = FakeSectionAnalysisService(
        error=ProviderConfigurationError("Chat provider secret 引用格式无效")
    )
    override_analysis_service(fake_service)

    response = client.post("/api/analysis/sections/sec-1", json={"language": "zh"})

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "AI_PROVIDER_NOT_CONFIGURED",
        "message": "尚未配置 AI 模型服务",
    }


def load_test_sqlite_vec(connection: sqlite3.Connection) -> None:
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def sqlite_url(database_path) -> str:
    return f"sqlite:///{database_path.as_posix()}"


def test_analyze_section_ch1_1_uses_demo_database_without_database_500(
    monkeypatch,
    tmp_path,
):
    import app.main as main_module
    from app.agents.analysis_agent import AnalysisAgent
    from app.api.analysis_controller import get_db_session
    from app.db.connection import initialize_runtime_database
    from app.db.demo_init import initialize_demo_database
    from app.db.orm import create_database_engine, create_session_factory

    database_path = tmp_path / "api-demo.sqlite3"
    database_url = sqlite_url(database_path)
    initialize_demo_database(
        database_url=database_url,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )

    def initialize_test_database():
        return initialize_runtime_database(
            database_url=database_url,
            sqlite_vec_loader=load_test_sqlite_vec,
            embedding_dimension=8,
        )

    monkeypatch.setattr(main_module, "initialize_runtime_database", initialize_test_database)

    engine = create_database_engine(
        database_url,
        sqlite_vec_loader=load_test_sqlite_vec,
    )
    session_factory = create_session_factory(engine)

    def override_db_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    async def fake_generate_section_analysis(
        self,
        *,
        section_context,
        language,
        model_name,
        prompt_version,
    ):
        del self, language, model_name, prompt_version
        unit = section_context.units[0]
        return {
            "section_id": section_context.section_id,
            "section_title": section_context.title,
            "status": "completed",
            "sentences": [
                {
                    "id": "s1",
                    "text": "人工智能正在改变教育资料的学习方式。",
                    "citations": [
                        {
                            "id": "c1",
                            "page": unit.page_number,
                            "document_unit_id": unit.document_unit_id,
                            "chunk_id": None,
                            "source_text": "人工智能技术取得了飞速发展",
                            "start_char": 3,
                            "end_char": 17,
                        }
                    ],
                }
            ],
            "source_pages": [
                {
                    "page": unit.page_number,
                    "document_unit_id": unit.document_unit_id,
                    "text": unit.text_content,
                }
            ],
        }

    monkeypatch.setattr(
        AnalysisAgent,
        "generate_section_analysis",
        fake_generate_section_analysis,
    )
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db_session] = override_db_session

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/analysis/sections/ch1-1",
                json={"language": "zh"},
            )
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["section_id"] == "ch1-1"
    assert body["data"]["content_json"]["sentences"][0]["citations"][0][
        "document_unit_id"
    ]
    assert body["data"]["content_json"]["source_pages"][0]["text"]


def test_analyze_section_ch1_1_returns_200_with_fake_provider(
    monkeypatch,
    tmp_path,
):
    import app.main as main_module
    from app.api.analysis_controller import get_db_session
    from app.db.connection import initialize_runtime_database
    from app.db.demo_init import initialize_demo_database
    from app.db.orm import create_database_engine, create_session_factory
    from app.providers.registry import ProviderRegistry

    database_path = tmp_path / "api-provider-demo.sqlite3"
    database_url = sqlite_url(database_path)
    initialize_demo_database(
        database_url=database_url,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )

    def initialize_test_database():
        return initialize_runtime_database(
            database_url=database_url,
            sqlite_vec_loader=load_test_sqlite_vec,
            embedding_dimension=8,
        )

    monkeypatch.setattr(main_module, "initialize_runtime_database", initialize_test_database)

    engine = create_database_engine(
        database_url,
        sqlite_vec_loader=load_test_sqlite_vec,
    )
    session_factory = create_session_factory(engine)

    def override_db_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    class FakeProvider:
        async def chat_completion(self, *args, **kwargs):
            del args, kwargs
            return ChatResult(
                content="""
                {
                  "section_id": "ch1-1",
                  "section_title": "1.1 背景介绍",
                  "status": "completed",
                  "sentences": [
                    {
                      "id": "s1",
                      "text": "人工智能正在改变教育资料的学习方式。",
                      "citations": [
                        {
                          "id": "c1",
                          "page": 1,
                          "document_unit_id": "demo-unit-page-1",
                          "chunk_id": null,
                          "source_text": "人工智能技术取得了飞速发展",
                          "start_char": 3,
                          "end_char": 17
                        }
                      ]
                    }
                  ],
                  "source_pages": [
                    {
                      "page": 1,
                      "document_unit_id": "demo-unit-page-1",
                      "text": "近年来，人工智能技术取得了飞速发展。"
                    }
                  ]
                }
                """
            )

    monkeypatch.setattr(ProviderRegistry, "get_active", lambda: FakeProvider())
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db_session] = override_db_session

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/analysis/sections/ch1-1",
                json={"language": "zh"},
            )
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["section_id"] == "ch1-1"
    assert body["data"]["content_json"]["sentences"][0]["citations"][0][
        "document_unit_id"
    ] == "demo-unit-page-1"

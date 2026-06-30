"""最小 agentic search API contract 测试。"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class FakeAgenticSearchService:
    def __init__(self, result: dict | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls: list[dict] = []

    async def answer(
        self,
        *,
        query: str | None = None,
        section_id: str | None = None,
        language: str = "zh",
        model_name: str | None = None,
        prompt_version: str = "agentic-search-v1",
        top_k: int = 5,
    ) -> dict:
        self.calls.append(
            {
                "query": query,
                "section_id": section_id,
                "language": language,
                "model_name": model_name,
                "prompt_version": prompt_version,
                "top_k": top_k,
            }
        )
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


def override_search_service(fake_service: FakeAgenticSearchService):
    from app.api.analysis_controller import get_agentic_search_service

    app.dependency_overrides[get_agentic_search_service] = lambda: fake_service


def traceable_search_result() -> dict:
    return {
        "query": "AI 如何帮助学习？",
        "section_id": None,
        "language": "zh",
        "content_markdown": "AI 可以帮助学生定位课程资料中的关键证据。",
        "content_json": {
            "status": "completed",
            "sentences": [
                {
                    "id": "s1",
                    "text": "AI 可以帮助学生定位课程资料中的关键证据。",
                    "citations": [
                        {
                            "id": "c1",
                            "page": 2,
                            "document_unit_id": "unit-1",
                            "chunk_id": "chunk-1",
                            "source_text": "AI supports evidence lookup",
                            "start_char": 0,
                            "end_char": 27,
                        }
                    ],
                }
            ],
            "source_pages": [
                {
                    "page": 2,
                    "document_unit_id": "unit-1",
                    "text": "AI supports evidence lookup in course documents.",
                }
            ],
        },
    }


def test_agentic_search_endpoint_returns_traceable_answer(client):
    fake_service = FakeAgenticSearchService(result=traceable_search_result())
    override_search_service(fake_service)

    response = client.post(
        "/api/analysis/search",
        json={"query": "AI 如何帮助学习？", "language": "zh", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["message"] == "检索回答完成"
    assert body["data"]["content_json"]["sentences"][0]["citations"][0]["chunk_id"] == "chunk-1"
    assert body["data"]["content_json"]["source_pages"][0]["document_unit_id"] == "unit-1"
    assert fake_service.calls[0]["query"] == "AI 如何帮助学习？"
    assert fake_service.calls[0]["top_k"] == 3


def test_agentic_search_endpoint_requires_query_or_section_id(client):
    response = client.post("/api/analysis/search", json={"language": "zh"})

    assert response.status_code == 422

import json
import re
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app.api.document_controller import get_db_session
from app.db.init_db import initialize_database, load_sqlite_vec_extension
from app.db.orm import create_database_engine, create_session_factory
from app.main import app
from app.providers.base import ChatResult
from app.providers.embedding_base import EmbeddingModelInfo
from app.providers.embedding_registry import EmbeddingProviderRegistry
from app.providers.registry import ProviderRegistry
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.repositories.section_repository import SectionRepository


def load_test_sqlite_vec(connection: sqlite3.Connection) -> None:
    connection.create_function("vec_version", 0, lambda: "test-sqlite-vec")


def test_upload_pdf_persists_units_and_returns_outline_candidates(
    tmp_path,
    text_two_pages_pdf_bytes,
):
    database_path = tmp_path / "pdf-flow.sqlite3"
    initialize_database(
        database_path=database_path,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )
    engine = create_database_engine(
        database_path,
        sqlite_vec_loader=load_test_sqlite_vec,
    )
    session_factory = create_session_factory(engine)

    def override_db_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db_session] = override_db_session

    try:
        client = TestClient(app)
        response = client.post(
            "/api/documents/upload",
            files={
                "file": (
                    "text_two_pages.pdf",
                    text_two_pages_pdf_bytes,
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["document_id"]
        assert payload["filename"] == "text_two_pages.pdf"
        assert payload["page_count"] == 2
        assert payload["status"] == "parsed"
        assert payload["page_index"]["page_count"] == 2
        assert [candidate["source"] for candidate in payload["outline_candidates"]] == [
            "pdf_outline",
            "llm_outline",
        ]
        assert payload["outline_candidates"][0]["status"] == "available"
        assert payload["outline_candidates"][0]["sections"]
        assert payload["outline_candidates"][1]["reason"] == "尚未配置 AI 模型服务"

        with session_factory() as session:
            document = DocumentRepository(session).get_by_id(payload["document_id"])
            units = DocumentUnitRepository(session).list_by_document_and_page_range(
                document_id=payload["document_id"],
                start_page=1,
                end_page=2,
            )
        assert document is not None
        assert document.page_count == 2
        assert [unit.page_number for unit in units] == [1, 2]
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_confirm_outline_endpoint_creates_formal_sections(
    tmp_path,
    text_two_pages_pdf_bytes,
):
    database_path = tmp_path / "confirm-flow.sqlite3"
    initialize_database(
        database_path=database_path,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )
    engine = create_database_engine(
        database_path,
        sqlite_vec_loader=load_test_sqlite_vec,
    )
    session_factory = create_session_factory(engine)

    def override_db_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db_session] = override_db_session

    try:
        client = TestClient(app)
        upload_response = client.post(
            "/api/documents/upload",
            files={
                "file": (
                    "text_two_pages.pdf",
                    text_two_pages_pdf_bytes,
                    "application/pdf",
                )
            },
        )
        document_id = upload_response.json()["data"]["document_id"]
        candidate = {
            "source": "pdf_outline",
            "status": "available",
            "sections": [
                {
                    "temp_id": "manual-1",
                    "title": "文本版 PDF 章节",
                    "level": 1,
                    "parent_temp_id": None,
                    "start_page": 1,
                    "end_page": 2,
                    "order_index": 0,
                }
            ],
        }

        first = client.post(
            f"/api/documents/{document_id}/outline/confirm",
            json={"candidate": candidate},
        )
        second = client.post(
            f"/api/documents/{document_id}/outline/confirm",
            json={"candidate": candidate},
        )

        assert first.status_code == 200
        assert second.status_code == 200
        first_data = first.json()["data"]
        second_data = second.json()["data"]
        assert first_data["sections"][0]["id"] == second_data["sections"][0]["id"]
        assert first_data["sections"][0]["title"] == "文本版 PDF 章节"
        assert first_data["section_unit_links_status"] == "metadata_fallback"
        assert first_data["chunk_status"] == "created"

        with session_factory() as session:
            sections = SectionRepository(session).list_by_document(document_id)
        assert len(sections) == 1
        assert sections[0].metadata_json["document_unit_ids"]
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_confirm_outline_indexes_chunks_with_fake_embedding_provider(
    tmp_path,
    text_two_pages_pdf_bytes,
):
    database_path = tmp_path / "confirm-embedding-flow.sqlite3"
    initialize_database(
        database_path=database_path,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )
    engine = create_database_engine(
        database_path,
        sqlite_vec_loader=load_test_sqlite_vec,
    )
    session_factory = create_session_factory(engine)

    class FakeEmbeddingProvider:
        async def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [[float(index + 1), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] for index, _ in enumerate(texts)]

        async def embed_query(self, query: str) -> list[float]:
            del query
            return [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        def get_model_info(self) -> EmbeddingModelInfo:
            return EmbeddingModelInfo(
                provider="fake",
                model_id="fake-embedding-8d",
                dimension=8,
            )

    def override_db_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db_session] = override_db_session
    EmbeddingProviderRegistry.activate(FakeEmbeddingProvider())

    try:
        client = TestClient(app)
        upload_response = client.post(
            "/api/documents/upload",
            files={
                "file": (
                    "text_two_pages.pdf",
                    text_two_pages_pdf_bytes,
                    "application/pdf",
                )
            },
        )
        document_id = upload_response.json()["data"]["document_id"]
        candidate = {
            "source": "llm_outline",
            "status": "available",
            "sections": [
                {
                    "temp_id": "ai-1",
                    "title": "AI 章节",
                    "level": 1,
                    "parent_temp_id": None,
                    "start_page": 1,
                    "end_page": 2,
                    "order_index": 0,
                }
            ],
        }

        response = client.post(
            f"/api/documents/{document_id}/outline/confirm",
            json={"candidate": candidate},
        )

        assert response.status_code == 200
        assert response.json()["data"]["embedding_status"] == "indexed"
        with session_factory() as session:
            embedding_count = session.connection().exec_driver_sql(
                "SELECT COUNT(*) FROM embedding_vectors"
            ).scalar_one()
            index_count = session.connection().exec_driver_sql(
                "SELECT COUNT(*) FROM chunk_embedding_index_entries"
            ).scalar_one()
        assert embedding_count > 0
        assert index_count == embedding_count
    finally:
        EmbeddingProviderRegistry.clear()
        app.dependency_overrides.clear()
        engine.dispose()


def test_confirmed_pdf_section_can_be_analyzed_with_traceable_citations(
    monkeypatch,
    tmp_path,
    text_two_pages_pdf_bytes,
):
    database_path = tmp_path / "pdf-section-analysis-flow.sqlite3"
    initialize_database(
        database_path=database_path,
        sqlite_vec_loader=load_test_sqlite_vec,
        embedding_dimension=8,
    )
    engine = create_database_engine(
        database_path,
        sqlite_vec_loader=load_test_sqlite_vec,
    )
    session_factory = create_session_factory(engine)

    class FakeChatProvider:
        async def chat_completion(self, messages, **kwargs):
            del kwargs
            user_message = messages[-1]["content"]
            section_id = re.search(r"Section ID: (.+)", user_message).group(1).strip()
            section_title = re.search(r"Section title: (.+)", user_message).group(1).strip()
            unit_match = re.search(
                r"\[document_unit_id=([^;]+); page=([^;]+);",
                user_message,
            )
            document_unit_id = unit_match.group(1)
            page_number = int(unit_match.group(2))
            return ChatResult(
                json.dumps(
                    {
                        "section_id": section_id,
                        "section_title": section_title,
                        "status": "completed",
                        "sentences": [
                            {
                                "id": "s1",
                                "text": "该小节解析可以追溯到上传 PDF 的原文。",
                                "citations": [
                                    {
                                        "id": "c1",
                                        "page": page_number,
                                        "document_unit_id": document_unit_id,
                                        "chunk_id": None,
                                        "source_text": "PDF 原文",
                                        "start_char": 0,
                                        "end_char": 6,
                                    }
                                ],
                            }
                        ],
                        "source_pages": [],
                    },
                    ensure_ascii=False,
                )
            )

    def override_db_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db_session] = override_db_session
    monkeypatch.setattr(ProviderRegistry, "get_active", lambda: FakeChatProvider())

    try:
        client = TestClient(app)
        upload_response = client.post(
            "/api/documents/upload",
            files={
                "file": (
                    "text_two_pages.pdf",
                    text_two_pages_pdf_bytes,
                    "application/pdf",
                )
            },
        )
        document_id = upload_response.json()["data"]["document_id"]
        candidate = {
            "source": "pdf_outline",
            "status": "available",
            "sections": [
                {
                    "temp_id": "analysis-1",
                    "title": "可解析小节",
                    "level": 1,
                    "parent_temp_id": None,
                    "start_page": 1,
                    "end_page": 2,
                    "order_index": 0,
                }
            ],
        }
        confirm_response = client.post(
            f"/api/documents/{document_id}/outline/confirm",
            json={"candidate": candidate},
        )
        section_id = confirm_response.json()["data"]["sections"][0]["id"]

        response = client.post(
            f"/api/analysis/sections/{section_id}",
            json={"language": "zh"},
        )

        assert response.status_code == 200
        body = response.json()
        content_json = body["data"]["content_json"]
        assert body["data"]["section_id"] == section_id
        assert content_json["section_id"] == section_id
        assert content_json["sentences"][0]["citations"][0]["document_unit_id"]
        assert content_json["source_pages"][0]["document_unit_id"] == content_json[
            "sentences"
        ][0]["citations"][0]["document_unit_id"]
        assert content_json["source_pages"][0]["text"]
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_confirmed_pdf_chunks_are_searchable_through_sqlite_vec_rag(
    monkeypatch,
    tmp_path,
    text_two_pages_pdf_bytes,
):
    pytest.importorskip("sqlite_vec")
    database_path = tmp_path / "pdf-rag-flow.sqlite3"
    initialize_database(
        database_path=database_path,
        sqlite_vec_loader=load_sqlite_vec_extension,
        embedding_dimension=8,
    )
    engine = create_database_engine(
        database_path,
        sqlite_vec_loader=load_sqlite_vec_extension,
    )
    session_factory = create_session_factory(engine)

    class FakeEmbeddingProvider:
        async def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] for _ in texts]

        async def embed_query(self, query: str) -> list[float]:
            del query
            return [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        def get_model_info(self) -> EmbeddingModelInfo:
            return EmbeddingModelInfo(
                provider="fake",
                model_id="fake-embedding-8d",
                dimension=8,
            )

    class FakeChatProvider:
        async def chat_completion(self, messages, **kwargs):
            del kwargs
            user_message = messages[-1]["content"]
            chunk_match = re.search(
                r"\[chunk_id=([^;]+); document_unit_id=([^;]+); page=([^;]+);",
                user_message,
            )
            chunk_id = chunk_match.group(1)
            document_unit_id = chunk_match.group(2)
            page_number = int(chunk_match.group(3))
            return ChatResult(
                json.dumps(
                    {
                        "query": "PDF 章节内容是什么？",
                        "section_id": None,
                        "status": "completed",
                        "sentences": [
                            {
                                "id": "s1",
                                "text": "RAG 检索到了确认大纲后生成的 PDF chunk。",
                                "citations": [
                                    {
                                        "id": "c1",
                                        "page": page_number,
                                        "document_unit_id": document_unit_id,
                                        "chunk_id": chunk_id,
                                        "source_text": "PDF chunk",
                                        "start_char": 0,
                                        "end_char": 9,
                                    }
                                ],
                            }
                        ],
                        "source_pages": [],
                    },
                    ensure_ascii=False,
                )
            )

    def override_db_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db_session] = override_db_session
    EmbeddingProviderRegistry.activate(FakeEmbeddingProvider())
    monkeypatch.setattr(ProviderRegistry, "get_active", lambda: FakeChatProvider())

    try:
        client = TestClient(app)
        upload_response = client.post(
            "/api/documents/upload",
            files={
                "file": (
                    "text_two_pages.pdf",
                    text_two_pages_pdf_bytes,
                    "application/pdf",
                )
            },
        )
        document_id = upload_response.json()["data"]["document_id"]
        candidate = {
            "source": "pdf_outline",
            "status": "available",
            "sections": [
                {
                    "temp_id": "rag-1",
                    "title": "可检索小节",
                    "level": 1,
                    "parent_temp_id": None,
                    "start_page": 1,
                    "end_page": 2,
                    "order_index": 0,
                }
            ],
        }
        confirm_response = client.post(
            f"/api/documents/{document_id}/outline/confirm",
            json={"candidate": candidate},
        )
        assert confirm_response.status_code == 200
        assert confirm_response.json()["data"]["embedding_status"] == "indexed"

        response = client.post(
            "/api/analysis/search",
            json={"query": "PDF 章节内容是什么？", "language": "zh", "top_k": 1},
        )

        assert response.status_code == 200
        content_json = response.json()["data"]["content_json"]
        citation = content_json["sentences"][0]["citations"][0]
        assert citation["chunk_id"]
        assert citation["document_unit_id"]
        assert content_json["source_pages"][0]["document_unit_id"] == citation[
            "document_unit_id"
        ]
    finally:
        EmbeddingProviderRegistry.clear()
        app.dependency_overrides.clear()
        engine.dispose()

"""显式 demo 数据初始化命令。

正常 FastAPI 启动只建 schema，不会调用本模块写入 demo 数据。
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config.settings import get_database_settings
from app.db.connection import initialize_runtime_database
from app.db.init_db import (
    DatabaseInitializationResult,
    SQLiteVecLoader,
    load_sqlite_vec_extension,
)
from app.db.orm import create_database_engine, create_session_factory
from app.entities import DocumentRecord, DocumentUnit, Section
from app.enums.document_file_type import DocumentFileType
from app.enums.document_status import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_unit_repository import DocumentUnitRepository
from app.repositories.section_repository import SectionRepository


DEMO_DOCUMENT_ID = "demo-pdf-1"
DEMO_DOCUMENT_UNIT_ID = "demo-unit-page-1"
DEMO_SECTION_ID = "ch1-1"
DEMO_SECTION_TITLE = "1.1 背景介绍"
DEMO_TEXT = (
    "近年来，人工智能技术取得了飞速发展。"
    "教育资料的学习方式正在被智能检索和小节解析改变。"
    "在法中国留学生需要同时处理专业概念、外语表述和中文理解。"
    "因此，小节解析需要把解释和原文证据一起展示。"
)


@dataclass(frozen=True)
class DemoInitializationResult:
    database: DatabaseInitializationResult
    document_id: str
    document_unit_id: str
    section_id: str


def initialize_demo_database(
    *,
    database_url: str | None = None,
    sqlite_vec_loader: SQLiteVecLoader = load_sqlite_vec_extension,
    embedding_dimension: int = 768,
) -> DemoInitializationResult:
    """创建 schema 并幂等写入最少 demo 数据。"""

    database_result = initialize_runtime_database(
        database_url=database_url,
        sqlite_vec_loader=sqlite_vec_loader,
        embedding_dimension=embedding_dimension,
    )
    settings = get_database_settings(database_url)
    engine = create_database_engine(
        settings.database_url,
        sqlite_vec_loader=sqlite_vec_loader,
    )
    session_factory = create_session_factory(engine)
    try:
        with session_factory() as session:
            seed_demo_data(session)
            session.commit()
    finally:
        engine.dispose()

    return DemoInitializationResult(
        database=database_result,
        document_id=DEMO_DOCUMENT_ID,
        document_unit_id=DEMO_DOCUMENT_UNIT_ID,
        section_id=DEMO_SECTION_ID,
    )


def seed_demo_data(session: Session) -> None:
    """幂等写入 demo document、document unit 和 ch1-1 section。"""

    document = DocumentRecord(
        id=DEMO_DOCUMENT_ID,
        workspace_id="demo-workspace",
        title="Demo PDF",
        original_filename="demo.pdf",
        file_type=DocumentFileType.PDF,
        file_path="data/uploads/demo.pdf",
        status=DocumentStatus.PARSED,
        page_count=1,
    )
    unit = DocumentUnit(
        id=DEMO_DOCUMENT_UNIT_ID,
        document_id=DEMO_DOCUMENT_ID,
        sequence_index=0,
        text_content=DEMO_TEXT,
        page_number=1,
        start_char=0,
        end_char=len(DEMO_TEXT),
        token_count=len(DEMO_TEXT),
        metadata_json={"source_type": "pdf", "demo": True},
        parser_name="DemoTextPDFParser",
        parser_version="0.1",
    )
    section = Section(
        id=DEMO_SECTION_ID,
        document_id=DEMO_DOCUMENT_ID,
        title=DEMO_SECTION_TITLE,
        level=2,
        order_index=0,
        start_page=1,
        end_page=1,
        metadata_json={"demo": True, "source": "demo_init"},
        parser_name="DemoSectionSeeder",
        parser_version="0.1",
    )

    DocumentRepository(session).save(document)
    DocumentUnitRepository(session).save(unit)
    SectionRepository(session).save(section)


def main() -> None:
    result = initialize_demo_database()
    print(
        "Demo data initialized: "
        f"database={result.database.database_path} "
        f"section_id={result.section_id}"
    )


if __name__ == "__main__":
    main()

"""
文档摄取服务，用于协调上传、解析、切分和入库流程。
"""
import os

from app.entities import DocumentRecord, DocumentUnit
from app.enums.document_file_type import DocumentFileType
from app.enums.document_status import DocumentStatus
from app.parsers.parser_factory import ParserFactory

# ---- Phase 3 依赖（暂未实现，待 ChunkService/EmbeddingService 就绪后取消注释） ----
# from app.services.chunk_service import ChunkService
# from app.services.embedding_service import EmbeddingService

# source_type → DocumentFileType 映射常量
SOURCE_TYPE_TO_FILE_TYPE: dict[str, DocumentFileType] = {
    "pdf": DocumentFileType.PDF,
    "word": DocumentFileType.DOCX,
    "ppt": DocumentFileType.PPTX,
    "image": DocumentFileType.IMAGE,
    "text": DocumentFileType.TEXT,
}


class DocumentIngestService:
    """安全文档摄取流水线：解析 → 实体构建 → 持久化（Phase 1 为纯内存模式）。"""

    def __init__(self, document_repository=None, document_unit_repository=None):
        """
        服务初始化。DB 仓库在 Phase 1 为可选注入，Phase 2 起变为必需。
        
        :param document_repository: DocumentRepository 实例，DB 团队交付后注入
        :param document_unit_repository: DocumentUnitRepository 实例，DB 团队交付后注入
        """
        # ---- 由 DB 团队交付后注入 ----
        self.document_repository = document_repository
        self.document_unit_repository = document_unit_repository

        # ---- Phase 3 依赖（待 ChunkService / EmbeddingService 就绪后取消注释） ----
        # self.chunk_service = ChunkService()
        # self.embedding_service = EmbeddingService()

    def ingest_document(
        self,
        filename: str,
        file_content: bytes,
        *,
        workspace_id: str = "",
        title: str | None = None,
        file_path: str = "",
        file_hash: str | None = None,
    ) -> dict:
        """
        贯穿整个文件流的摄取流水线 (Pipeline) — Phase 1 同步内存模式。
        
        Phase 1 不执行 DB 写入；Phase 2 将在此方法内通过 Repository 完成持久化，
        届时方法签名将改为 `async def` 以支持异步 DB I/O。

        :param filename: 文件名（含扩展名）
        :param file_content: 文件二进制数据
        :param workspace_id: 所属工作区 ID
        :param title: 文档标题，不传则从文件名推导
        :param file_path: 原始文件在本地 uploads 目录下的路径
        :param file_hash: 原始文件哈希值
        :return: 解析结果字典，包含 document_record 和 document_units
        """
        # ---- Step 1: 通过工厂匹配解析器并提取 PageIndex 原始单页文本 ----
        parser = ParserFactory.get_parser(filename)
        parsed_pages = parser.parse(file_content)

        # ---- Step 2: 基于 PageIndex 构造 DocumentRecord ----
        # 从第一页的 metadata 推断文件类型
        source_type = (
            parsed_pages[0]["metadata"]["source_type"]
            if parsed_pages and "metadata" in parsed_pages[0]
            else "other"
        )
        file_type = SOURCE_TYPE_TO_FILE_TYPE.get(source_type, DocumentFileType.OTHER)

        # 推导文档标题
        if title is None:
            title = os.path.splitext(filename)[0]

        document_record = DocumentRecord(
            workspace_id=workspace_id,
            title=title,
            original_filename=filename,
            file_type=file_type,
            file_path=file_path,
            file_hash=file_hash,
            status=DocumentStatus.PARSED,
            page_count=len(parsed_pages),
        )

        # ---- Phase 2: DB 团队交付 DocumentRepository 后取消注释 ----
        # self.document_repository.save(document_record)

        # ---- Step 3: 基于 PageIndex 构造 DocumentUnit 列表 ----
        document_units: list[DocumentUnit] = []
        cumulative_offset = 0

        for i, page in enumerate(parsed_pages):
            content_len = len(page.get("content", ""))

            unit = DocumentUnit(
                document_id=document_record.id,
                sequence_index=i,
                text_content=page.get("content", ""),
                page_number=page.get("page_number"),
                start_char=cumulative_offset,
                end_char=cumulative_offset + content_len,
                token_count=None,  # 后续由 TokenService 计算
                metadata_json=page.get("metadata"),
                raw_content_json={
                    k: v for k, v in page.items()
                    if k != "content"  # content 已存入 text_content，避免重复
                },
                parser_name=page.get("parser_name"),
                parser_version=page.get("parser_version"),
            )
            document_units.append(unit)
            cumulative_offset += content_len

            # ---- Phase 2: DB 团队交付 DocumentUnitRepository 后取消注释 ----
            # self.document_unit_repository.save(unit)

        # ---- Step 4 & 5: （Phase 3 占位，ChunkService / EmbeddingService 就绪后启用） ----
        # chunks = self.chunk_service.split_pages_into_chunks(parsed_pages)
        # embedded_chunks = await self.embedding_service.gen_embeddings(chunks)

        # ---- 构造返回结果 ----
        page_index_preview: list[dict[str, object]] = []
        for p in parsed_pages:
            preview_item: dict[str, object] = {
                "page_number": p["page_number"],
                "char_count": p["char_count"],
            }
            if "metadata" in p:
                preview_item["source_type"] = p["metadata"].get("source_type", "unknown")
            page_index_preview.append(preview_item)

        return {
            "filename": filename,
            "total_pages": len(parsed_pages),
            "status": "parsed_successfully",
            "page_index_preview": page_index_preview,
            "document_record": document_record,
            "document_units": document_units,
        }

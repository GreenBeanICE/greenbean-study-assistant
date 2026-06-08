"""
文档摄取服务，用于协调上传、解析、切分和入库流程。
"""
from app.parsers.parser_factory import ParserFactory

# 先注释掉未完成的服务导入，防止报错
# from app.services.chunk_service import ChunkService
# from app.services.embedding_service import EmbeddingService


class DocumentIngestService:
    def __init__(self):
        # 临时注释，等后面写到这两个服务时再解开
        # self.chunk_service = ChunkService()
        # self.embedding_service = EmbeddingService()
        pass

    async def ingest_document(self, filename: str, file_content: bytes):
        """
        贯穿整个文件流的摄取流水线 (Pipeline)
        
        :param filename: 文件名（含扩展名）
        :param file_content: 文件二进制数据
        :return: 解析结果字典
        """
        # Step 1: 通过工厂匹配解析器并提取 PageIndex 原始单页文本
        parser = ParserFactory.get_parser(filename)
        parsed_pages = parser.parse(file_content)
        
        # Step 2 & 3: 临时 Mock 占位，确保链路能跑通
        # chunks = self.chunk_service.split_pages_into_chunks(parsed_pages)
        # embedded_chunks = await self.embedding_service.gen_embeddings(chunks)
        
        # 构造返回结果，包含 PageIndex 预览和来源类型
        page_index_preview = []
        for p in parsed_pages:
            preview_item = {
                "page_number": p["page_number"],
                "char_count": p["char_count"],
            }
            # 如果有 metadata，添加 source_type
            if "metadata" in p:
                preview_item["source_type"] = p["metadata"].get("source_type", "unknown")
            page_index_preview.append(preview_item)
        
        return {
            "filename": filename,
            "total_pages": len(parsed_pages),
            "status": "parsed_successfully",
            "page_index_preview": page_index_preview,
        }

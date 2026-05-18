# 文档摄取服务占位文件，后续用于协调上传、解析、切分和入库流程。
# backend-python/app/services/document_ingest_service.py
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
        """
        # Step 1: 通过工厂匹配解析器并提取 PageIndex 原始单页文本
        parser = ParserFactory.get_parser(filename)
        parsed_pages = parser.parse(file_content)
        
        # Step 2 & 3: 临时 Mock 占位，确保链路能跑通
        # chunks = self.chunk_service.split_pages_into_chunks(parsed_pages)
        # embedded_chunks = await self.embedding_service.gen_embeddings(chunks)
        
        # 目前先返回 PageIndex 的元数据结构，供前端验证和测试
        return {
            "filename": filename,
            "total_pages": len(parsed_pages),
            "status": "parsed_successfully",
            "page_index_preview": [
                {
                    "page_number": p["page_number"], 
                    "char_count": p["char_count"]
                } for p in parsed_pages
            ]
        }
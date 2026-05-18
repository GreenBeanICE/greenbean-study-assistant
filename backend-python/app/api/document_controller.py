# 文档接口控制器占位文件，后续用于提供文档上传、列表和详情相关 API。
# backend-python/app/api/document_controller.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.document_ingest_service import DocumentIngestService

router = APIRouter(prefix="/documents", tags=["Documents"])

# 依赖注入：确保每个请求能正确拿到 IngestService 实例
def get_ingest_service() -> DocumentIngestService:
    return DocumentIngestService()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    ingest_service: DocumentIngestService = Depends(get_ingest_service)
):
    """
    接收前端通过 FormData 传来的文件，调用 Service 流水线进行解析与导入
    """
    try:
        # 读取文件二级制流
        file_content = await file.read()
        
        # 进入导入流水线
        result = await ingest_service.ingest_document(file.filename, file_content)
        
        return {
            "code": 200,
            "message": "文件上传并解析成功",
            "data": result
        }
        
    except ValueError as ve:
        # 捕获类似“不支持的文件格式”等业务异常
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # 捕获系统底层或未知异常
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
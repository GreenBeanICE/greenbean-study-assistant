"""
文档接口控制器，提供文档上传、列表和详情相关 API。
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.document_ingest_service import DocumentIngestService
from app.utils.file_utils import is_supported, get_extension

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
    接收前端通过 FormData 传来的文件，调用 Service 流水线进行解析与导入。
    
    支持的文件格式:
    - 文档: PDF(.pdf), Word(.docx), PPT(.pptx), 纯文本(.txt/.md)
    - 图片: JPG/JPEG, PNG, WEBP
    """
    # 检查文件名是否存在
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    # 检查文件格式是否支持
    if not is_supported(file.filename):
        ext = get_extension(file.filename)
        raise HTTPException(
            status_code=400,
            detail=f"暂不支持 {ext} 格式。支持的格式: PDF(.pdf), Word(.docx), PPT(.pptx), 纯文本(.txt/.md), 图片(.jpg/.jpeg/.png/.webp)"
        )
    
    try:
        # 读取文件二进制流
        file_content = await file.read()
        
        # 检查文件是否为空
        if not file_content:
            raise HTTPException(status_code=400, detail="文件内容为空")
        
        # 进入导入流水线
        result = await ingest_service.ingest_document(file.filename, file_content)
        
        return {
            "code": 200,
            "message": "文件上传并解析成功",
            "data": result
        }
        
    except ValueError as ve:
        # 捕获类似"不支持的文件格式"等业务异常
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        # 重新抛出已处理的 HTTP 异常
        raise
    except Exception as e:
        # 捕获系统底层或未知异常
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

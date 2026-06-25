# Python 后端应用入口占位文件，后续用于创建 FastAPI 应用并注册路由。
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import document_controller
from app.providers.embedding_registry import EmbeddingProviderRegistry
from app.providers.embedding_setup import initialize_embedding_provider


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期：启动时装配 Embedding Provider，关闭时清理进程内状态。"""

    setup_result = initialize_embedding_provider()
    fastapi_app.state.embedding_available = setup_result.available
    fastapi_app.state.embedding_error = setup_result.error
    try:
        yield
    finally:
        EmbeddingProviderRegistry.clear()


app = FastAPI(title="Greenbean Study Assistant API", lifespan=lifespan)

# 注册文档上传解析的路由
app.include_router(document_controller.router, prefix="/api")

# ... 你的其他 main.py 配置（如 CORS、其他路由等）

# Python 后端应用入口占位文件，后续用于创建 FastAPI 应用并注册路由。
# backend-python/app/main.py
from fastapi import FastAPI
from app.api import document_controller  # 引入你的控制器

app = FastAPI(title="Greenbean Study Assistant API")

# 注册文档上传解析的路由
app.include_router(document_controller.router, prefix="/api")

# ... 你的其他 main.py 配置（如 CORS、其他路由等）
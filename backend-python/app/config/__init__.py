# 标记 backend-python\app\config 为 Python 包，便于后续按模块导入。
from app.config.embedding_settings import GoogleEmbeddingSettings

__all__ = ["GoogleEmbeddingSettings"]

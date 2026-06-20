"""Embedding Provider 公共接口与错误类型。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class EmbeddingProviderError(RuntimeError):
    """Embedding Provider 调用失败。"""


class EmbeddingValidationError(EmbeddingProviderError):
    """Embedding 请求或响应不符合约束。"""


@dataclass(frozen=True)
class EmbeddingModelInfo:
    """当前 Embedding 模型的稳定元数据。"""

    provider: str
    model_id: str
    dimension: int


class EmbeddingProvider(ABC):
    """Embedding 服务统一异步接口。"""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """为待索引文档生成向量。"""

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """为检索查询生成向量。"""

    @abstractmethod
    def get_model_info(self) -> EmbeddingModelInfo:
        """返回 Provider、模型和向量维度。"""

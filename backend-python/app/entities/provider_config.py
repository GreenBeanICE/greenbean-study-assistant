from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose


class ProviderConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="Provider 配置唯一 ID。")
    name: str = Field(..., description="内部标识，如 'my-deepseek'。")
    api_mode: ApiMode = Field(..., description="API 模式，决定使用的 SDK 实现类。")
    api_key: str = Field(..., description="API 密钥。")
    api_host: str = Field(..., description="API 主机地址，如 'https://api.deepseek.com'。")
    api_path: str = Field(default="/v1/chat/completions", description="API 路径。")
    model_id: str = Field(..., description="模型 ID，如 'deepseek-chat'。")
    display_name: str = Field(..., description="前端展示名称。")
    context_window: int = Field(default=65536, description="上下文窗口大小（token 数）。")
    max_output_tokens: int = Field(default=8192, description="最大输出 token 数。")
    is_active: bool = Field(default=False, description="是否为当前激活的 provider。")
    purpose: Purpose = Field(..., description="用途：chat 或 embedding。")
    embedding_dimension: int | None = Field(default=None, description="向量维度，仅 embedding 用。")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间。")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="最后更新时间。")

    @model_validator(mode="after")
    def _validate_dimension_by_purpose(self) -> "ProviderConfig":
        if self.purpose == Purpose.EMBEDDING:
            if self.embedding_dimension is None or self.embedding_dimension <= 0:
                raise ValueError("embedding 配置必须提供正整数 embedding_dimension")
        elif self.purpose == Purpose.CHAT and self.embedding_dimension is not None:
            raise ValueError("chat 配置不能设置 embedding_dimension")
        return self

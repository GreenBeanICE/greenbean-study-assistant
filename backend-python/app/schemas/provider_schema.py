from pydantic import BaseModel, Field, model_validator

from app.enums.api_mode import ApiMode
from app.enums.purpose import Purpose


class ProviderConfigCreateRequest(BaseModel):
    name: str = Field(..., description="内部标识，如 'my-deepseek'。")
    api_mode: ApiMode = Field(..., description="API 模式。")
    api_key: str = Field(..., description="API 密钥。")
    api_host: str = Field(..., description="API 主机地址。")
    api_path: str = Field(default="/v1/chat/completions", description="API 路径。")
    model_id: str = Field(..., description="模型 ID。")
    display_name: str = Field(..., description="前端展示名称。")
    context_window: int = Field(default=65536, description="上下文窗口大小。")
    max_output_tokens: int = Field(default=8192, description="最大输出 token 数。")
    purpose: Purpose = Field(..., description="用途：chat 或 embedding。")
    embedding_dimension: int | None = Field(default=None, description="向量维度，仅 embedding 用。")

    @model_validator(mode="after")
    def validate_dimension_by_purpose(self) -> "ProviderConfigCreateRequest":
        if self.purpose == Purpose.EMBEDDING:
            if self.embedding_dimension is None or self.embedding_dimension <= 0:
                raise ValueError("embedding 配置必须提供正整数 embedding_dimension")
        elif self.embedding_dimension is not None:
            raise ValueError("chat 配置不能设置 embedding_dimension")
        return self


class ProviderConfigUpdateRequest(BaseModel):
    name: str | None = Field(default=None, description="内部标识。")
    api_mode: ApiMode | None = Field(default=None, description="API 模式。")
    api_key: str | None = Field(default=None, description="API 密钥。")
    api_host: str | None = Field(default=None, description="API 主机地址。")
    api_path: str | None = Field(default=None, description="API 路径。")
    model_id: str | None = Field(default=None, description="模型 ID。")
    display_name: str | None = Field(default=None, description="前端展示名称。")
    context_window: int | None = Field(default=None, description="上下文窗口大小。")
    max_output_tokens: int | None = Field(default=None, description="最大输出 token 数。")
    purpose: Purpose | None = Field(default=None, description="用途。")
    embedding_dimension: int | None = Field(default=None, description="向量维度。")

    @model_validator(mode="after")
    def validate_dimension_by_purpose(self) -> "ProviderConfigUpdateRequest":
        if self.purpose == Purpose.EMBEDDING:
            if self.embedding_dimension is not None and self.embedding_dimension <= 0:
                raise ValueError("embedding 配置必须提供正整数 embedding_dimension")
        elif self.purpose == Purpose.CHAT and self.embedding_dimension is not None:
            raise ValueError("chat 配置不能设置 embedding_dimension")
        return self


class ProviderConfigResponse(BaseModel):
    id: str = Field(..., description="配置 ID。")
    name: str = Field(..., description="内部标识。")
    api_mode: ApiMode = Field(..., description="API 模式。")
    api_host: str = Field(..., description="API 主机地址。")
    api_path: str = Field(..., description="API 路径。")
    model_id: str = Field(..., description="模型 ID。")
    display_name: str = Field(..., description="展示名称。")
    context_window: int = Field(..., description="上下文窗口大小。")
    max_output_tokens: int = Field(..., description="最大输出 token 数。")
    purpose: Purpose = Field(..., description="用途。")
    embedding_dimension: int | None = Field(default=None, description="向量维度。")
    is_active: bool = Field(..., description="是否当前激活。")
    created_at: str = Field(..., description="创建时间。")
    updated_at: str = Field(..., description="最后更新时间。")


class ProviderActivateResponse(BaseModel):
    id: str = Field(..., description="已激活的配置 ID。")
    name: str = Field(..., description="内部标识。")
    display_name: str = Field(..., description="展示名称。")
    model_id: str = Field(..., description="模型 ID。")

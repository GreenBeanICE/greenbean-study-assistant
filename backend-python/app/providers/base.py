from abc import ABC, abstractmethod


class ChatResult:
    def __init__(self, content: str) -> None:
        self.content = content


class ProviderConfigurationError(RuntimeError):
    """AI Provider 配置无法安全加载或解析。"""


class AIProvider(ABC):

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> ChatResult:
        ...

from abc import ABC, abstractmethod


class ChatResult:
    def __init__(self, content: str) -> None:
        self.content = content


class EmbeddingResult:
    def __init__(self, embeddings: list[list[float]], model: str) -> None:
        self.embeddings = embeddings
        self.model = model


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

    @abstractmethod
    async def create_embedding(
        self,
        input: str | list[str],
        model: str | None = None,
    ) -> EmbeddingResult:
        ...

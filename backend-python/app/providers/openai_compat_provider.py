from openai import AsyncOpenAI

from app.entities.provider_config import ProviderConfig
from app.providers.base import AIProvider, ChatResult, EmbeddingResult


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.api_host.rstrip("/"),
        )

    async def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> ChatResult:
        kwargs = dict(
            model=model or self.config.model_id,
            messages=messages,
            temperature=temperature,
        )
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = self.config.max_output_tokens
        if response_format is not None:
            kwargs["response_format"] = response_format

        response = await self._client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        return ChatResult(content=content)

    async def create_embedding(
        self,
        input: str | list[str],
        model: str | None = None,
    ) -> EmbeddingResult:
        if model is None:
            raise ValueError("Embedding model is required")

        response = await self._client.embeddings.create(model=model, input=input)
        return EmbeddingResult(
            embeddings=[item.embedding for item in response.data],
            model=response.model,
        )

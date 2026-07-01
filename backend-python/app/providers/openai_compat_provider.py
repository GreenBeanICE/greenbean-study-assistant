from openai import AsyncOpenAI

from app.entities.provider_config import ProviderConfig
from app.providers.base import AIProvider, ChatResult
from app.providers.chat_provider_secrets import resolve_chat_api_key


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self._client = AsyncOpenAI(
            api_key=resolve_chat_api_key(config.api_key),
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

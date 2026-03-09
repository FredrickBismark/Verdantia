"""LLM service with multi-provider abstraction.

Supported providers: Ollama, Anthropic, OpenAI, Venice, OpenRouter, Custom.
Implementation in Phase 2.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from enum import StrEnum

from pydantic import BaseModel


class LLMProvider(StrEnum):
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    VENICE = "venice"
    OPENROUTER = "openrouter"
    CUSTOM = "custom"


class LLMConfig(BaseModel):
    provider: LLMProvider
    model: str
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.3
    max_tokens: int = 4096


class LLMClient(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        images: list[str] | None = None,
        response_format: str | None = None,
    ) -> str: ...

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncIterator[str]: ...


def create_llm_client(config: LLMConfig) -> LLMClient:
    """Factory function to create the appropriate LLM client.

    Implementation coming in Phase 2.
    """
    raise NotImplementedError("LLM client implementation coming in Phase 2")

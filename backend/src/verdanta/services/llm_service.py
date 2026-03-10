"""LLM service with multi-provider abstraction.

Supported providers: Ollama, Anthropic, OpenAI, Venice, OpenRouter, Custom.
All LLM calls go through this service — never call provider APIs directly.
"""

import json as json_mod
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from enum import StrEnum

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


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


class LLMResponse(BaseModel):
    text: str
    model: str
    provider: str
    duration_ms: int
    tokens_used: int | None = None


class LLMClient(ABC):
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        images: list[str] | None = None,
        response_format: str | None = None,
    ) -> LLMResponse: ...

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncIterator[str]: ...

    async def test_connection(self) -> bool:
        """Send a minimal prompt to verify the provider is reachable."""
        try:
            resp = await self.generate("Say 'ok'.", system="Respond with only 'ok'.")
            return len(resp.text) > 0
        except Exception:
            logger.exception("LLM connection test failed")
            return False


class OllamaClient(LLMClient):
    """Client for local Ollama instance."""

    @property
    def _base_url(self) -> str:
        return self.config.base_url or "http://localhost:11434"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        images: list[str] | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        start = time.monotonic()
        payload: dict = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }
        if system:
            payload["system"] = system
        if images:
            payload["images"] = images
        if response_format == "json":
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self._base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()

        duration_ms = int((time.monotonic() - start) * 1000)
        tokens = data.get("eval_count")
        return LLMResponse(
            text=data["response"],
            model=self.config.model,
            provider=LLMProvider.OLLAMA,
            duration_ms=duration_ms,
            tokens_used=tokens,
        )

    async def stream(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        payload: dict = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }
        if system:
            payload["system"] = system

        async with (
            httpx.AsyncClient(timeout=120.0) as client,
            client.stream("POST", f"{self._base_url}/api/generate", json=payload) as resp,
        ):
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    chunk = json_mod.loads(line)
                    if chunk.get("response"):
                        yield chunk["response"]

    async def list_models(self) -> list[dict]:
        """Query Ollama for locally available models."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self._base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
        return [
            {"id": m["name"], "name": m["name"], "size": m.get("size")}
            for m in data.get("models", [])
        ]


class OpenAICompatibleClient(LLMClient):
    """Client for OpenAI-compatible APIs (OpenAI, Venice, OpenRouter, Custom)."""

    @property
    def _base_url(self) -> str:
        defaults = {
            LLMProvider.OPENAI: "https://api.openai.com/v1",
            LLMProvider.VENICE: "https://api.venice.ai/api/v1",
            LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
        }
        return self.config.base_url or defaults.get(
            self.config.provider, "http://localhost:8080/v1"
        )

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        if self.config.provider == LLMProvider.OPENROUTER:
            headers["HTTP-Referer"] = "https://verdanta.local"
            headers["X-Title"] = "Verdanta"
        return headers

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        images: list[str] | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        start = time.monotonic()
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})

        if images:
            content: list[dict] = [{"type": "text", "text": prompt}]
            for img in images:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img}"},
                    }
                )
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": prompt})

        payload: dict = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()

        duration_ms = int((time.monotonic() - start) * 1000)
        choice = data["choices"][0]
        usage = data.get("usage", {})
        return LLMResponse(
            text=choice["message"]["content"],
            model=data.get("model", self.config.model),
            provider=str(self.config.provider),
            duration_ms=duration_ms,
            tokens_used=usage.get("total_tokens"),
        )

    async def stream(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
        }

        async with (
            httpx.AsyncClient(timeout=120.0) as client,
            client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
            ) as resp,
        ):
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    chunk = json_mod.loads(line[6:])
                    delta = chunk["choices"][0].get("delta", {})
                    if delta.get("content"):
                        yield delta["content"]


class AnthropicClient(LLMClient):
    """Client for the Anthropic Messages API."""

    @property
    def _base_url(self) -> str:
        return self.config.base_url or "https://api.anthropic.com"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        images: list[str] | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        start = time.monotonic()

        content: list[dict] = []
        if images:
            for img in images:
                content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img,
                        },
                    }
                )
        content.append({"type": "text", "text": prompt})

        payload: dict = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "messages": [{"role": "user", "content": content}],
        }
        if system:
            payload["system"] = system
        if self.config.temperature != 0.3:
            payload["temperature"] = self.config.temperature

        headers = {
            "x-api-key": self.config.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/v1/messages",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        duration_ms = int((time.monotonic() - start) * 1000)
        text_blocks = [b["text"] for b in data["content"] if b["type"] == "text"]
        usage = data.get("usage", {})
        return LLMResponse(
            text="".join(text_blocks),
            model=data.get("model", self.config.model),
            provider=LLMProvider.ANTHROPIC,
            duration_ms=duration_ms,
            tokens_used=(usage.get("input_tokens", 0) + usage.get("output_tokens", 0)),
        )

    async def stream(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        payload: dict = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        if system:
            payload["system"] = system

        headers = {
            "x-api-key": self.config.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        async with (
            httpx.AsyncClient(timeout=120.0) as client,
            client.stream(
                "POST",
                f"{self._base_url}/v1/messages",
                json=payload,
                headers=headers,
            ) as resp,
        ):
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    event = json_mod.loads(line[6:])
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("text"):
                            yield delta["text"]


def create_llm_client(config: LLMConfig) -> LLMClient:
    """Factory function to create the appropriate LLM client."""
    if config.provider == LLMProvider.OLLAMA:
        return OllamaClient(config)
    elif config.provider == LLMProvider.ANTHROPIC:
        return AnthropicClient(config)
    elif config.provider in (
        LLMProvider.OPENAI,
        LLMProvider.VENICE,
        LLMProvider.OPENROUTER,
        LLMProvider.CUSTOM,
    ):
        return OpenAICompatibleClient(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


async def get_llm_config_from_settings(
    db_settings: dict[str, str],
) -> LLMConfig:
    """Build LLMConfig from app settings (key-value pairs from DB)."""
    from verdanta.core.config import settings as app_settings

    provider = db_settings.get("llm_provider", app_settings.llm_default_provider)
    model = db_settings.get("llm_model", app_settings.llm_default_model)

    api_key_map = {
        "anthropic": app_settings.anthropic_api_key,
        "openai": app_settings.openai_api_key,
        "venice": app_settings.venice_api_key,
        "openrouter": app_settings.openrouter_api_key,
    }
    api_key = db_settings.get(f"{provider}_api_key") or api_key_map.get(provider)

    base_url_map = {
        "ollama": app_settings.ollama_base_url,
    }
    base_url = db_settings.get(f"{provider}_base_url") or base_url_map.get(provider)

    return LLMConfig(
        provider=LLMProvider(provider),
        model=model,
        api_key=api_key,
        base_url=base_url,
    )

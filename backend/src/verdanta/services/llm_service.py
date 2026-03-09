"""LLM service with multi-provider abstraction.

Supported providers: Ollama, Anthropic, OpenAI, Venice, OpenRouter, Custom.
All LLM calls go through LLMService — never call provider APIs directly.
Every interaction is logged to llm_interactions table for transparency.
"""

import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from enum import StrEnum

import httpx
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.config import settings
from verdanta.models.llm import LLMInteraction


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
    tokens_used: int | None = None
    duration_ms: int | None = None


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
    ) -> str: ...

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncIterator[str]: ...


class OllamaClient(LLMClient):
    """Client for local Ollama instances."""

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        images: list[str] | None = None,
        response_format: str | None = None,
    ) -> str:
        base_url = self.config.base_url or settings.ollama_base_url
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
            resp = await client.post(f"{base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json()["response"]

    async def stream(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        base_url = self.config.base_url or settings.ollama_base_url
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

        async with httpx.AsyncClient(timeout=120.0) as client, client.stream(
            "POST", f"{base_url}/api/generate", json=payload
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    import json

                    data = json.loads(line)
                    if token := data.get("response", ""):
                        yield token


class OpenAICompatibleClient(LLMClient):
    """Client for OpenAI-compatible APIs (OpenAI, Venice, OpenRouter, Custom)."""

    def _get_base_url(self) -> str:
        if self.config.base_url:
            return self.config.base_url
        urls = {
            LLMProvider.OPENAI: "https://api.openai.com/v1",
            LLMProvider.VENICE: "https://api.venice.ai/api/v1",
            LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
        }
        return urls.get(self.config.provider, "https://api.openai.com/v1")

    def _get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        images: list[str] | None = None,
        response_format: str | None = None,
    ) -> str:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})

        if images:
            content: list[dict] = [{"type": "text", "text": prompt}]
            for img in images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img}"},
                })
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
                f"{self._get_base_url()}/chat/completions",
                json=payload,
                headers=self._get_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

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

        async with httpx.AsyncClient(timeout=120.0) as client, client.stream(
            "POST",
            f"{self._get_base_url()}/chat/completions",
            json=payload,
            headers=self._get_headers(),
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    import json

                    data = json.loads(line[6:])
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    if content := delta.get("content", ""):
                        yield content


class AnthropicClient(LLMClient):
    """Client for the Anthropic Messages API."""

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        images: list[str] | None = None,
        response_format: str | None = None,
    ) -> str:
        api_key = self.config.api_key or settings.anthropic_api_key
        if not api_key:
            raise ValueError("Anthropic API key not configured")

        base_url = self.config.base_url or "https://api.anthropic.com"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        content: list[dict] = []
        if images:
            for img in images:
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": img},
                })
        content.append({"type": "text", "text": prompt})

        payload: dict = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [{"role": "user", "content": content}],
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url}/v1/messages",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def stream(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        api_key = self.config.api_key or settings.anthropic_api_key
        if not api_key:
            raise ValueError("Anthropic API key not configured")

        base_url = self.config.base_url or "https://api.anthropic.com"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload: dict = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client, client.stream(
            "POST",
            f"{base_url}/v1/messages",
            json=payload,
            headers=headers,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    import json

                    data = json.loads(line[6:])
                    if data.get("type") == "content_block_delta" and (
                        text := data.get("delta", {}).get("text", "")
                    ):
                        yield text


def create_llm_client(config: LLMConfig) -> LLMClient:
    """Factory function to create the appropriate LLM client."""
    match config.provider:
        case LLMProvider.OLLAMA:
            return OllamaClient(config)
        case LLMProvider.ANTHROPIC:
            return AnthropicClient(config)
        case LLMProvider.OPENAI | LLMProvider.VENICE | LLMProvider.OPENROUTER | LLMProvider.CUSTOM:
            return OpenAICompatibleClient(config)
        case _:
            raise ValueError(f"Unknown provider: {config.provider}")


class LLMService:
    """High-level LLM service that handles config resolution, client creation,
    interaction logging, and graceful degradation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _resolve_config(self) -> LLMConfig:
        """Resolve LLM config from app settings or fall back to env defaults."""
        from sqlalchemy import select

        from verdanta.models.settings import AppSettings

        result = await self.db.execute(select(AppSettings))
        settings_map: dict[str, str] = {}
        for s in result.scalars().all():
            settings_map[s.key] = s.value

        provider_str = settings_map.get("llm_provider", settings.llm_default_provider)
        model = settings_map.get("llm_model", settings.llm_default_model)

        provider = LLMProvider(provider_str)
        api_key: str | None = None
        base_url: str | None = None

        if provider == LLMProvider.ANTHROPIC:
            api_key = settings_map.get("anthropic_api_key") or settings.anthropic_api_key
        elif provider == LLMProvider.OPENAI:
            api_key = settings_map.get("openai_api_key") or settings.openai_api_key
        elif provider == LLMProvider.VENICE:
            api_key = settings_map.get("venice_api_key") or settings.venice_api_key
        elif provider == LLMProvider.OPENROUTER:
            api_key = settings_map.get("openrouter_api_key") or settings.openrouter_api_key
        elif provider == LLMProvider.OLLAMA:
            base_url = settings.ollama_base_url

        return LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        garden_id: int | None = None,
        planting_id: int | None = None,
        interaction_type: str = "general",
        images: list[str] | None = None,
        response_format: str | None = None,
        config_override: LLMConfig | None = None,
    ) -> LLMResponse:
        """Generate an LLM response and log the interaction."""
        config = config_override or await self._resolve_config()
        client = create_llm_client(config)

        start = time.monotonic()
        error_msg: str | None = None
        response_text = ""
        status = "completed"

        try:
            response_text = await client.generate(
                prompt=prompt,
                system=system,
                images=images,
                response_format=response_format,
            )
        except Exception as e:
            error_msg = str(e)
            status = "error"
            raise

        finally:
            duration = int((time.monotonic() - start) * 1000)
            if garden_id is not None:
                interaction = LLMInteraction(
                    garden_id=garden_id,
                    planting_id=planting_id,
                    interaction_type=interaction_type,
                    user_prompt=prompt,
                    system_context=system or "",
                    response=response_text,
                    model_used=config.model,
                    provider=config.provider,
                    status=status,
                    error_message=error_msg,
                    duration_ms=duration,
                )
                self.db.add(interaction)
                await self.db.flush()

        return LLMResponse(
            text=response_text,
            model=config.model,
            provider=config.provider,
            duration_ms=int((time.monotonic() - start) * 1000),
        )

    async def stream(
        self,
        prompt: str,
        system: str | None = None,
        config_override: LLMConfig | None = None,
    ) -> AsyncIterator[str]:
        """Stream an LLM response."""
        config = config_override or await self._resolve_config()
        client = create_llm_client(config)
        async for token in client.stream(prompt=prompt, system=system):
            yield token

    async def test_connection(self, config: LLMConfig) -> dict:
        """Test if an LLM provider is reachable with the given config."""
        client = create_llm_client(config)
        start = time.monotonic()
        try:
            response = await client.generate(
                prompt="Say 'hello' in one word.",
                system="You are a test assistant. Reply with a single word.",
            )
            duration = int((time.monotonic() - start) * 1000)
            return {
                "status": "success",
                "response": response.strip(),
                "duration_ms": duration,
                "model": config.model,
                "provider": config.provider,
            }
        except Exception as e:
            duration = int((time.monotonic() - start) * 1000)
            return {
                "status": "error",
                "error": str(e),
                "duration_ms": duration,
                "model": config.model,
                "provider": config.provider,
            }

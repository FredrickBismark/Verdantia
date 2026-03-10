"""Tests for the LLM service layer."""

from unittest.mock import AsyncMock

from verdanta.services.llm_service import (
    AnthropicClient,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    OllamaClient,
    OpenAICompatibleClient,
    create_llm_client,
    get_llm_config_from_settings,
)


def test_create_llm_client_ollama() -> None:
    config = LLMConfig(provider=LLMProvider.OLLAMA, model="llama3:8b")
    client = create_llm_client(config)
    assert isinstance(client, OllamaClient)


def test_create_llm_client_anthropic() -> None:
    config = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-sonnet-4-20250514")
    client = create_llm_client(config)
    assert isinstance(client, AnthropicClient)


def test_create_llm_client_openai() -> None:
    config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o")
    client = create_llm_client(config)
    assert isinstance(client, OpenAICompatibleClient)


def test_create_llm_client_venice() -> None:
    config = LLMConfig(provider=LLMProvider.VENICE, model="llama-3.3-70b")
    client = create_llm_client(config)
    assert isinstance(client, OpenAICompatibleClient)


def test_create_llm_client_openrouter() -> None:
    config = LLMConfig(provider=LLMProvider.OPENROUTER, model="test")
    client = create_llm_client(config)
    assert isinstance(client, OpenAICompatibleClient)


def test_create_llm_client_custom() -> None:
    config = LLMConfig(
        provider=LLMProvider.CUSTOM, model="test", base_url="http://localhost:8080/v1"
    )
    client = create_llm_client(config)
    assert isinstance(client, OpenAICompatibleClient)


def test_ollama_base_url_default() -> None:
    config = LLMConfig(provider=LLMProvider.OLLAMA, model="test")
    client = OllamaClient(config)
    assert client._base_url == "http://localhost:11434"


def test_ollama_base_url_custom() -> None:
    config = LLMConfig(provider=LLMProvider.OLLAMA, model="test", base_url="http://myhost:11434")
    client = OllamaClient(config)
    assert client._base_url == "http://myhost:11434"


def test_openai_base_url_defaults() -> None:
    for provider, expected in [
        (LLMProvider.OPENAI, "https://api.openai.com/v1"),
        (LLMProvider.VENICE, "https://api.venice.ai/api/v1"),
        (LLMProvider.OPENROUTER, "https://openrouter.ai/api/v1"),
    ]:
        config = LLMConfig(provider=provider, model="test")
        client = OpenAICompatibleClient(config)
        assert client._base_url == expected


def test_openai_headers_with_api_key() -> None:
    config = LLMConfig(provider=LLMProvider.OPENAI, model="test", api_key="sk-test123")
    client = OpenAICompatibleClient(config)
    headers = client._headers()
    assert headers["Authorization"] == "Bearer sk-test123"


def test_openrouter_headers() -> None:
    config = LLMConfig(provider=LLMProvider.OPENROUTER, model="test", api_key="or-key")
    client = OpenAICompatibleClient(config)
    headers = client._headers()
    assert "HTTP-Referer" in headers
    assert "X-Title" in headers


def test_llm_config_defaults() -> None:
    config = LLMConfig(provider=LLMProvider.OLLAMA, model="test")
    assert config.temperature == 0.3
    assert config.max_tokens == 4096
    assert config.api_key is None
    assert config.base_url is None


def test_llm_response_model() -> None:
    resp = LLMResponse(text="Hello", model="test", provider="ollama", duration_ms=100)
    assert resp.tokens_used is None
    assert resp.duration_ms == 100


async def test_get_llm_config_from_settings_defaults() -> None:
    config = await get_llm_config_from_settings({})
    assert config.provider == LLMProvider.OLLAMA
    assert config.model == "llama3:8b"


async def test_get_llm_config_from_settings_override() -> None:
    config = await get_llm_config_from_settings(
        {"llm_provider": "anthropic", "llm_model": "claude-sonnet-4-20250514"}
    )
    assert config.provider == LLMProvider.ANTHROPIC
    assert config.model == "claude-sonnet-4-20250514"


async def test_test_connection_success() -> None:
    config = LLMConfig(provider=LLMProvider.OLLAMA, model="test")
    client = OllamaClient(config)
    client.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=LLMResponse(text="ok", model="test", provider="ollama", duration_ms=50)
    )
    assert await client.test_connection() is True


async def test_test_connection_failure() -> None:
    config = LLMConfig(provider=LLMProvider.OLLAMA, model="test")
    client = OllamaClient(config)
    client.generate = AsyncMock(side_effect=Exception("connection refused"))  # type: ignore[method-assign]
    assert await client.test_connection() is False

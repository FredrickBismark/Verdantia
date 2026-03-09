"""Tests for LLM service — tests use mocked HTTP responses."""

from unittest.mock import AsyncMock, MagicMock, patch

from verdanta.services.llm_service import (
    AnthropicClient,
    LLMConfig,
    LLMProvider,
    LLMService,
    OllamaClient,
    OpenAICompatibleClient,
    create_llm_client,
)


def test_create_llm_client_ollama():
    config = LLMConfig(provider=LLMProvider.OLLAMA, model="llama3:8b")
    client = create_llm_client(config)
    assert isinstance(client, OllamaClient)


def test_create_llm_client_anthropic():
    config = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-sonnet-4-20250514")
    client = create_llm_client(config)
    assert isinstance(client, AnthropicClient)


def test_create_llm_client_openai():
    config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o")
    client = create_llm_client(config)
    assert isinstance(client, OpenAICompatibleClient)


def test_create_llm_client_venice():
    config = LLMConfig(provider=LLMProvider.VENICE, model="llama-3.3-70b")
    client = create_llm_client(config)
    assert isinstance(client, OpenAICompatibleClient)


def test_create_llm_client_openrouter():
    config = LLMConfig(provider=LLMProvider.OPENROUTER, model="meta/llama3")
    client = create_llm_client(config)
    assert isinstance(client, OpenAICompatibleClient)


async def test_ollama_generate():
    config = LLMConfig(
        provider=LLMProvider.OLLAMA,
        model="llama3:8b",
        base_url="http://localhost:11434",
    )
    client = OllamaClient(config)

    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Hello world"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_http:
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value = mock_instance

        result = await client.generate("Say hello")
        assert result == "Hello world"


async def test_openai_generate():
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
        api_key="test-key",
    )
    client = OpenAICompatibleClient(config)

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Hello from OpenAI"}}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_http:
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value = mock_instance

        result = await client.generate("Say hello", system="Be brief")
        assert result == "Hello from OpenAI"


async def test_anthropic_generate():
    config = LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-sonnet-4-20250514",
        api_key="test-key",
    )
    client = AnthropicClient(config)

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "content": [{"text": "Hello from Claude"}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_http:
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value = mock_instance

        result = await client.generate("Say hello")
        assert result == "Hello from Claude"


async def test_llm_service_test_connection():
    config = LLMConfig(
        provider=LLMProvider.OLLAMA,
        model="llama3:8b",
        base_url="http://localhost:11434",
    )

    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "hello"}
    mock_response.raise_for_status = MagicMock()

    db = AsyncMock()
    service = LLMService(db)

    with patch("httpx.AsyncClient") as mock_http:
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value = mock_instance

        result = await service.test_connection(config)
        assert result["status"] == "success"
        assert result["response"] == "hello"
        assert result["model"] == "llama3:8b"


async def test_llm_service_test_connection_error():
    config = LLMConfig(
        provider=LLMProvider.OLLAMA,
        model="llama3:8b",
        base_url="http://localhost:11434",
    )

    db = AsyncMock()
    service = LLMService(db)

    with patch("httpx.AsyncClient") as mock_http:
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(side_effect=Exception("Connection refused"))
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value = mock_instance

        result = await service.test_connection(config)
        assert result["status"] == "error"
        assert "Connection refused" in result["error"]

"""Tests for LLM-related settings endpoints."""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


async def test_get_provider_presets_structure(app_client: AsyncClient) -> None:
    resp = await app_client.get("/api/v1/settings/llm/providers")
    assert resp.status_code == 200
    body = resp.json()
    presets = body["data"]

    for provider in ["ollama", "anthropic", "openai", "venice", "openrouter"]:
        assert provider in presets
        p = presets[provider]
        assert "base_url" in p
        assert "requires_api_key" in p
        assert "models" in p
        assert isinstance(p["models"], list)

    # Ollama should not require API key
    assert presets["ollama"]["requires_api_key"] is False
    # Anthropic should require API key
    assert presets["anthropic"]["requires_api_key"] is True


async def test_llm_test_connection_success(app_client: AsyncClient) -> None:
    mock_client = AsyncMock()
    mock_client.test_connection = AsyncMock(return_value=True)

    with patch(
        "verdanta.routes.app_settings.create_llm_client",
        return_value=mock_client,
    ):
        resp = await app_client.post(
            "/api/v1/settings/llm/test",
            json={"provider": "ollama", "model": "llama3:8b"},
        )

    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ok"


async def test_llm_test_connection_failure(app_client: AsyncClient) -> None:
    mock_client = AsyncMock()
    mock_client.test_connection = AsyncMock(return_value=False)

    with patch(
        "verdanta.routes.app_settings.create_llm_client",
        return_value=mock_client,
    ):
        resp = await app_client.post(
            "/api/v1/settings/llm/test",
            json={"provider": "ollama", "model": "nonexistent"},
        )

    assert resp.status_code == 502


async def test_ollama_models_success(app_client: AsyncClient) -> None:
    mock_models = [
        {"id": "llama3:8b", "name": "llama3:8b", "size": 4000000000},
        {"id": "mistral:7b", "name": "mistral:7b", "size": 3500000000},
    ]

    with patch(
        "verdanta.routes.app_settings.OllamaClient"
    ) as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.list_models = AsyncMock(return_value=mock_models)
        mock_cls.return_value = mock_instance

        resp = await app_client.get("/api/v1/settings/llm/ollama/models")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 2
    assert body["data"][0]["id"] == "llama3:8b"


async def test_ollama_models_connection_error(app_client: AsyncClient) -> None:
    with patch(
        "verdanta.routes.app_settings.OllamaClient"
    ) as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.list_models = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_cls.return_value = mock_instance

        resp = await app_client.get("/api/v1/settings/llm/ollama/models")

    assert resp.status_code == 502
    assert "Ollama" in resp.json()["detail"]

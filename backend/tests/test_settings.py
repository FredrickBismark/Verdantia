from httpx import AsyncClient


async def test_get_settings_empty(app_client: AsyncClient) -> None:
    resp = await app_client.get("/api/v1/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert body["data"] == []
    assert "count" in body
    assert body["count"] == 0


async def test_update_setting(app_client: AsyncClient) -> None:
    # Create a new setting
    resp = await app_client.put(
        "/api/v1/settings/llm_provider",
        json={"value": "ollama"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert body["data"]["key"] == "llm_provider"
    assert body["data"]["value"] == "ollama"
    assert "updated_at" in body["data"]

    # Update the same setting
    resp = await app_client.put(
        "/api/v1/settings/llm_provider",
        json={"value": "anthropic"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["value"] == "anthropic"

    # Verify it shows in the list
    resp = await app_client.get("/api/v1/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["key"] == "llm_provider"
    assert body["data"][0]["value"] == "anthropic"


async def test_get_provider_presets(app_client: AsyncClient) -> None:
    resp = await app_client.get("/api/v1/settings/llm/providers")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    presets = body["data"]
    # Check that expected providers are present
    assert "ollama" in presets
    assert "anthropic" in presets
    assert "openai" in presets
    # Check structure of a preset
    ollama = presets["ollama"]
    assert "base_url" in ollama
    assert "requires_api_key" in ollama
    assert "models" in ollama
    assert ollama["requires_api_key"] is False

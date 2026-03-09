from httpx import AsyncClient

GARDEN_DATA = {"name": "Test Garden", "latitude": 40.7128, "longitude": -74.006}


async def _create_garden(client: AsyncClient, data: dict | None = None) -> dict:
    """Helper to create a garden and return the response JSON."""
    resp = await client.post("/api/v1/gardens", json=data or GARDEN_DATA)
    assert resp.status_code == 201
    return resp.json()


async def test_create_garden(app_client: AsyncClient) -> None:
    body = await _create_garden(app_client)
    assert "data" in body
    garden = body["data"]
    assert garden["name"] == "Test Garden"
    assert garden["latitude"] == 40.7128
    assert garden["longitude"] == -74.006
    assert "id" in garden
    assert "created_at" in garden
    assert "updated_at" in garden


async def test_list_gardens(app_client: AsyncClient) -> None:
    await _create_garden(app_client, {"name": "Garden A", "latitude": 1.0, "longitude": 2.0})
    await _create_garden(app_client, {"name": "Garden B", "latitude": 3.0, "longitude": 4.0})

    resp = await app_client.get("/api/v1/gardens")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "count" in body
    assert body["count"] == 2
    assert len(body["data"]) == 2


async def test_get_garden(app_client: AsyncClient) -> None:
    created = await _create_garden(app_client)
    garden_id = created["data"]["id"]

    resp = await app_client.get(f"/api/v1/gardens/{garden_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["id"] == garden_id
    assert body["data"]["name"] == "Test Garden"


async def test_update_garden(app_client: AsyncClient) -> None:
    created = await _create_garden(app_client)
    garden_id = created["data"]["id"]

    resp = await app_client.put(
        f"/api/v1/gardens/{garden_id}",
        json={"name": "Updated Garden", "usda_zone": "7b"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["name"] == "Updated Garden"
    assert body["data"]["usda_zone"] == "7b"
    # Unchanged fields should remain the same
    assert body["data"]["latitude"] == 40.7128


async def test_delete_garden(app_client: AsyncClient) -> None:
    created = await _create_garden(app_client)
    garden_id = created["data"]["id"]

    resp = await app_client.delete(f"/api/v1/gardens/{garden_id}")
    assert resp.status_code == 204

    resp = await app_client.get(f"/api/v1/gardens/{garden_id}")
    assert resp.status_code == 404


async def test_get_garden_not_found(app_client: AsyncClient) -> None:
    resp = await app_client.get("/api/v1/gardens/999")
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body

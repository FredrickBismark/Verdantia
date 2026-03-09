from httpx import AsyncClient

PLANT_DATA = {"common_name": "Tomato"}


async def _create_plant(client: AsyncClient, data: dict | None = None) -> dict:
    """Helper to create a plant species and return the response JSON."""
    resp = await client.post("/api/v1/plants", json=data or PLANT_DATA)
    assert resp.status_code == 201
    return resp.json()


async def test_create_plant(app_client: AsyncClient) -> None:
    body = await _create_plant(app_client)
    assert "data" in body
    plant = body["data"]
    assert plant["common_name"] == "Tomato"
    assert "id" in plant
    assert "curation_status" in plant
    assert "created_at" in plant
    assert "updated_at" in plant


async def test_list_plants(app_client: AsyncClient) -> None:
    await _create_plant(app_client, {"common_name": "Tomato"})
    await _create_plant(app_client, {"common_name": "Basil"})

    resp = await app_client.get("/api/v1/plants")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "count" in body
    assert body["count"] == 2
    assert len(body["data"]) == 2


async def test_list_plants_search(app_client: AsyncClient) -> None:
    await _create_plant(app_client, {"common_name": "Tomato"})
    await _create_plant(app_client, {"common_name": "Basil"})
    await _create_plant(app_client, {"common_name": "Cherry Tomato"})

    resp = await app_client.get("/api/v1/plants", params={"search": "Tomato"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    names = {p["common_name"] for p in body["data"]}
    assert names == {"Tomato", "Cherry Tomato"}


async def test_get_plant(app_client: AsyncClient) -> None:
    created = await _create_plant(app_client)
    plant_id = created["data"]["id"]

    resp = await app_client.get(f"/api/v1/plants/{plant_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["id"] == plant_id
    assert body["data"]["common_name"] == "Tomato"
    # Detail response includes dossier_sections and data_sources
    assert "dossier_sections" in body["data"]
    assert "data_sources" in body["data"]


async def test_update_plant(app_client: AsyncClient) -> None:
    created = await _create_plant(app_client)
    plant_id = created["data"]["id"]

    resp = await app_client.put(
        f"/api/v1/plants/{plant_id}",
        json={"scientific_name": "Solanum lycopersicum", "sun_requirement": "full_sun"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["scientific_name"] == "Solanum lycopersicum"
    assert body["data"]["sun_requirement"] == "full_sun"
    assert body["data"]["common_name"] == "Tomato"


async def test_delete_plant(app_client: AsyncClient) -> None:
    created = await _create_plant(app_client)
    plant_id = created["data"]["id"]

    resp = await app_client.delete(f"/api/v1/plants/{plant_id}")
    assert resp.status_code == 204

    resp = await app_client.get(f"/api/v1/plants/{plant_id}")
    assert resp.status_code == 404


async def test_get_plant_not_found(app_client: AsyncClient) -> None:
    resp = await app_client.get("/api/v1/plants/999")
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body

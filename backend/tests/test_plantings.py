from httpx import AsyncClient

GARDEN_DATA = {"name": "Test Garden", "latitude": 40.7128, "longitude": -74.006}
PLANT_DATA = {"common_name": "Tomato"}


async def _create_garden(client: AsyncClient) -> int:
    """Create a garden and return its id."""
    resp = await client.post("/api/v1/gardens", json=GARDEN_DATA)
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def _create_plant(client: AsyncClient) -> int:
    """Create a plant species and return its id."""
    resp = await client.post("/api/v1/plants", json=PLANT_DATA)
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def _create_planting(
    client: AsyncClient, garden_id: int, species_id: int, **extra: object
) -> dict:
    """Create a planting under a garden and return the response JSON."""
    data = {"species_id": species_id, **extra}
    resp = await client.post(f"/api/v1/gardens/{garden_id}/plantings", json=data)
    assert resp.status_code == 201
    return resp.json()


async def test_create_planting(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    species_id = await _create_plant(app_client)

    body = await _create_planting(app_client, garden_id, species_id)
    assert "data" in body
    planting = body["data"]
    assert planting["garden_id"] == garden_id
    assert planting["species_id"] == species_id
    assert planting["status"] == "planned"
    assert "id" in planting
    assert "created_at" in planting
    assert "updated_at" in planting


async def test_list_plantings(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    species_id = await _create_plant(app_client)

    await _create_planting(app_client, garden_id, species_id, bed_or_location="Bed A")
    await _create_planting(app_client, garden_id, species_id, bed_or_location="Bed B")

    resp = await app_client.get(f"/api/v1/gardens/{garden_id}/plantings")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "count" in body
    assert body["count"] == 2
    assert len(body["data"]) == 2


async def test_get_planting(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    species_id = await _create_plant(app_client)
    created = await _create_planting(app_client, garden_id, species_id)
    planting_id = created["data"]["id"]

    resp = await app_client.get(f"/api/v1/plantings/{planting_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["id"] == planting_id
    assert body["data"]["garden_id"] == garden_id
    assert body["data"]["species_id"] == species_id


async def test_update_planting(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    species_id = await _create_plant(app_client)
    created = await _create_planting(app_client, garden_id, species_id)
    planting_id = created["data"]["id"]

    resp = await app_client.put(
        f"/api/v1/plantings/{planting_id}",
        json={"status": "active", "bed_or_location": "Raised Bed 1", "quantity": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["status"] == "active"
    assert body["data"]["bed_or_location"] == "Raised Bed 1"
    assert body["data"]["quantity"] == 5


async def test_delete_planting(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    species_id = await _create_plant(app_client)
    created = await _create_planting(app_client, garden_id, species_id)
    planting_id = created["data"]["id"]

    resp = await app_client.delete(f"/api/v1/plantings/{planting_id}")
    assert resp.status_code == 204

    resp = await app_client.get(f"/api/v1/plantings/{planting_id}")
    assert resp.status_code == 404


async def test_get_planting_not_found(app_client: AsyncClient) -> None:
    resp = await app_client.get("/api/v1/plantings/999")
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body


async def test_cascade_delete_garden_removes_plantings(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    species_id = await _create_plant(app_client)
    await _create_planting(app_client, garden_id, species_id)
    await _create_planting(app_client, garden_id, species_id)

    resp = await app_client.delete(f"/api/v1/gardens/{garden_id}")
    assert resp.status_code == 204

    # Plantings should be gone via cascade
    resp = await app_client.get(f"/api/v1/gardens/{garden_id}/plantings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert len(body["data"]) == 0

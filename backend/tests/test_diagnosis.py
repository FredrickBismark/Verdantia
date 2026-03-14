from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

GARDEN_DATA = {"name": "Diagnosis Garden", "latitude": 40.7128, "longitude": -74.006}
PLANT_DATA = {"common_name": "Tomato", "scientific_name": "Solanum lycopersicum"}


async def _create_garden(client: AsyncClient) -> dict:
    resp = await client.post("/api/v1/gardens", json=GARDEN_DATA)
    assert resp.status_code == 201
    return resp.json()["data"]


async def _create_plant(client: AsyncClient) -> dict:
    resp = await client.post("/api/v1/plants", json=PLANT_DATA)
    assert resp.status_code == 201
    return resp.json()["data"]


async def _create_planting(client: AsyncClient, garden_id: int, species_id: int) -> dict:
    resp = await client.post(
        f"/api/v1/gardens/{garden_id}/plantings",
        json={"species_id": species_id, "quantity": 3},
    )
    assert resp.status_code == 201
    return resp.json()["data"]


async def test_diagnose_planting_not_found(app_client: AsyncClient) -> None:
    resp = await app_client.post(
        "/api/v1/plantings/9999/advisor/diagnose",
        json={"photo_id": 1},
    )
    assert resp.status_code == 404
    assert "Planting not found" in resp.json()["detail"]


async def test_diagnose_photo_not_found(app_client: AsyncClient) -> None:
    garden = await _create_garden(app_client)
    plant = await _create_plant(app_client)
    planting = await _create_planting(app_client, garden["id"], plant["id"])

    resp = await app_client.post(
        f"/api/v1/plantings/{planting['id']}/advisor/diagnose",
        json={"photo_id": 9999},
    )
    assert resp.status_code == 404
    assert "Photo not found" in resp.json()["detail"]

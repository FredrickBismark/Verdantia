from datetime import UTC, datetime

from httpx import AsyncClient

GARDEN_DATA = {"name": "Sensor Garden", "latitude": 40.7128, "longitude": -74.006}


async def _create_garden(client: AsyncClient) -> dict:
    resp = await client.post("/api/v1/gardens", json=GARDEN_DATA)
    assert resp.status_code == 201
    return resp.json()["data"]


async def test_manual_sensor_entry(app_client: AsyncClient) -> None:
    garden = await _create_garden(app_client)
    reading_data = {
        "sensor_id": "temp-001",
        "sensor_type": "temperature",
        "value": 22.5,
        "unit": "°C",
        "location": "Bed A",
    }
    resp = await app_client.post(
        f"/api/v1/gardens/{garden['id']}/sensors/reading", json=reading_data
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "data" in body
    data = body["data"]
    assert data["sensor_id"] == "temp-001"
    assert data["sensor_type"] == "temperature"
    assert data["value"] == 22.5
    assert data["unit"] == "°C"
    assert data["location"] == "Bed A"


async def test_sensor_readings(app_client: AsyncClient) -> None:
    garden = await _create_garden(app_client)
    for i in range(3):
        await app_client.post(
            f"/api/v1/gardens/{garden['id']}/sensors/reading",
            json={
                "sensor_id": "humidity-001",
                "sensor_type": "humidity",
                "value": 50.0 + i,
                "unit": "%",
            },
        )

    resp = await app_client.get(
        f"/api/v1/gardens/{garden['id']}/sensors/humidity-001/readings"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 3
    assert len(body["data"]) == 3


async def test_list_sensors(app_client: AsyncClient) -> None:
    garden = await _create_garden(app_client)
    # Add readings for two different sensors
    await app_client.post(
        f"/api/v1/gardens/{garden['id']}/sensors/reading",
        json={
            "sensor_id": "temp-001",
            "sensor_type": "temperature",
            "value": 22.0,
            "unit": "°C",
        },
    )
    await app_client.post(
        f"/api/v1/gardens/{garden['id']}/sensors/reading",
        json={
            "sensor_id": "moisture-001",
            "sensor_type": "soil_moisture",
            "value": 45.0,
            "unit": "%",
        },
    )

    resp = await app_client.get(f"/api/v1/gardens/{garden['id']}/sensors")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    sensor_ids = {s["sensor_id"] for s in body["data"]}
    assert "temp-001" in sensor_ids
    assert "moisture-001" in sensor_ids


async def test_list_sensors_garden_not_found(app_client: AsyncClient) -> None:
    resp = await app_client.get("/api/v1/gardens/9999/sensors")
    assert resp.status_code == 404


async def test_sensor_status(app_client: AsyncClient) -> None:
    garden = await _create_garden(app_client)
    await app_client.post(
        f"/api/v1/gardens/{garden['id']}/sensors/reading",
        json={
            "sensor_id": "temp-002",
            "sensor_type": "temperature",
            "value": 18.0,
            "unit": "°C",
        },
    )

    resp = await app_client.get(f"/api/v1/gardens/{garden['id']}/sensors/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    status = body["data"][0]
    assert "sensor_id" in status
    assert "health" in status
    assert "connected" in status
    assert "reading_count" in status


async def test_sensor_status_garden_not_found(app_client: AsyncClient) -> None:
    resp = await app_client.get("/api/v1/gardens/9999/sensors/status")
    assert resp.status_code == 404


async def test_empty_sensors_list(app_client: AsyncClient) -> None:
    garden = await _create_garden(app_client)
    resp = await app_client.get(f"/api/v1/gardens/{garden['id']}/sensors")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["data"] == []

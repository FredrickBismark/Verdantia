"""Tests for the calendar events CRUD endpoints."""

from httpx import AsyncClient

GARDEN_DATA = {"name": "Test Garden", "latitude": 40.0, "longitude": -74.0}


async def _create_garden(client: AsyncClient) -> int:
    resp = await client.post("/api/v1/gardens", json=GARDEN_DATA)
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def _create_event(
    client: AsyncClient, garden_id: int, **extra: object
) -> dict:
    data = {
        "event_type": "watering",
        "title": "Water tomatoes",
        "scheduled_date": "2026-04-15",
        **extra,
    }
    resp = await client.post(f"/api/v1/gardens/{garden_id}/events", json=data)
    assert resp.status_code == 201
    return resp.json()


async def test_create_event(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    body = await _create_event(app_client, garden_id)
    event = body["data"]
    assert event["garden_id"] == garden_id
    assert event["event_type"] == "watering"
    assert event["title"] == "Water tomatoes"
    assert event["completed"] is False
    assert "id" in event


async def test_list_events(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    await _create_event(app_client, garden_id, title="Event 1")
    await _create_event(app_client, garden_id, title="Event 2")

    resp = await app_client.get(f"/api/v1/gardens/{garden_id}/events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert len(body["data"]) == 2


async def test_list_events_filter_by_type(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    await _create_event(app_client, garden_id, event_type="watering")
    await _create_event(app_client, garden_id, event_type="fertilizing")

    resp = await app_client.get(
        f"/api/v1/gardens/{garden_id}/events?event_type=watering"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["data"][0]["event_type"] == "watering"


async def test_get_event(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    created = await _create_event(app_client, garden_id)
    event_id = created["data"]["id"]

    resp = await app_client.get(f"/api/v1/events/{event_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == event_id


async def test_get_event_not_found(app_client: AsyncClient) -> None:
    resp = await app_client.get("/api/v1/events/999")
    assert resp.status_code == 404


async def test_update_event(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    created = await _create_event(app_client, garden_id)
    event_id = created["data"]["id"]

    resp = await app_client.put(
        f"/api/v1/events/{event_id}",
        json={"title": "Updated title", "priority": "high"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["title"] == "Updated title"
    assert body["data"]["priority"] == "high"
    assert body["data"]["event_type"] == "watering"  # unchanged


async def test_delete_event(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    created = await _create_event(app_client, garden_id)
    event_id = created["data"]["id"]

    resp = await app_client.delete(f"/api/v1/events/{event_id}")
    assert resp.status_code == 204

    resp = await app_client.get(f"/api/v1/events/{event_id}")
    assert resp.status_code == 404


async def test_complete_event(app_client: AsyncClient) -> None:
    garden_id = await _create_garden(app_client)
    created = await _create_event(app_client, garden_id)
    event_id = created["data"]["id"]

    resp = await app_client.post(f"/api/v1/events/{event_id}/complete")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["completed"] is True
    assert body["data"]["completed_at"] is not None

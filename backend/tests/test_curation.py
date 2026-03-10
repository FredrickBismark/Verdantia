"""Tests for the plant curation pipeline and curate endpoint."""

import json
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from verdanta.services.llm_service import LLMResponse
from verdanta.services.plant_curation_service import (
    _build_plant_context,
    _parse_dossier_response,
)

GARDEN_DATA = {"name": "Test Garden", "latitude": 40.0, "longitude": -74.0}
PLANT_DATA = {"common_name": "Tomato", "scientific_name": "Solanum lycopersicum"}

MOCK_DOSSIER_JSON = json.dumps(
    {
        "overview": {"content": "Tomato overview text.", "confidence": "high"},
        "growing_conditions": {"content": "Full sun, well-drained soil.", "confidence": "high"},
        "planting_guide": {"content": "Start indoors 6-8 weeks before.", "confidence": "medium"},
        "care_maintenance": {"content": "Water regularly.", "confidence": "high"},
        "harvest_storage": {"content": "Pick when red.", "confidence": "high"},
        "pests_diseases": {"content": "Watch for blight.", "confidence": "medium"},
        "companion_planting": {"content": "Plant with basil.", "confidence": "medium"},
    }
)

MOCK_LLM_RESPONSE = LLMResponse(
    text=MOCK_DOSSIER_JSON,
    model="test-model",
    provider="ollama",
    duration_ms=500,
    tokens_used=100,
)


def test_parse_dossier_response_valid() -> None:
    result = _parse_dossier_response(MOCK_DOSSIER_JSON)
    assert "overview" in result
    assert result["overview"]["confidence"] == "high"
    assert "content" in result["growing_conditions"]


def test_parse_dossier_response_with_markdown_fences() -> None:
    wrapped = f"```json\n{MOCK_DOSSIER_JSON}\n```"
    result = _parse_dossier_response(wrapped)
    assert "overview" in result


def test_parse_dossier_response_invalid() -> None:
    import pytest

    with pytest.raises((json.JSONDecodeError, ValueError)):
        _parse_dossier_response("not json at all")


def test_build_plant_context() -> None:
    from verdanta.models.plant import PlantSpecies

    plant = PlantSpecies(
        id=1,
        common_name="Tomato",
        scientific_name="Solanum lycopersicum",
        sun_requirement="Full Sun",
    )
    ctx = _build_plant_context(plant)
    assert "Tomato" in ctx
    assert "Full Sun" in ctx
    assert "Known plant attributes:" in ctx


async def test_curate_endpoint_with_mock_llm(app_client: AsyncClient) -> None:
    """Integration test: create a garden + plant, then curate with mocked LLM."""
    # Create garden first (needed for LLM interaction FK)
    resp = await app_client.post("/api/v1/gardens", json=GARDEN_DATA)
    assert resp.status_code == 201

    # Create plant
    resp = await app_client.post("/api/v1/plants", json=PLANT_DATA)
    assert resp.status_code == 201
    plant_id = resp.json()["data"]["id"]

    # Mock the LLM client and OpenFarm
    mock_client = AsyncMock()
    mock_client.generate = AsyncMock(return_value=MOCK_LLM_RESPONSE)

    with (
        patch(
            "verdanta.services.plant_curation_service.create_llm_client",
            return_value=mock_client,
        ),
        patch(
            "verdanta.services.plant_curation_service.fetch_openfarm_crop",
            return_value=None,
        ),
    ):
        resp = await app_client.post(f"/api/v1/plants/{plant_id}/curate")

    assert resp.status_code == 200
    body = resp.json()
    plant_detail = body["data"]

    # Verify curation status
    assert plant_detail["curation_status"] == "curated"
    assert plant_detail["curation_model"] == "test-model"

    # Verify dossier sections created
    sections = plant_detail["dossier_sections"]
    assert len(sections) == 7
    section_types = [s["section_type"] for s in sections]
    assert "overview" in section_types
    assert "companion_planting" in section_types

    # Verify confidence levels
    overview = next(s for s in sections if s["section_type"] == "overview")
    assert overview["confidence"] == "high"
    assert "Tomato overview text." in overview["content"]


async def test_curate_endpoint_plant_not_found(app_client: AsyncClient) -> None:
    resp = await app_client.post("/api/v1/plants/999/curate")
    assert resp.status_code == 404


async def test_curate_endpoint_llm_failure(app_client: AsyncClient) -> None:
    """Test that curate returns 502 when LLM fails."""
    resp = await app_client.post("/api/v1/gardens", json=GARDEN_DATA)
    assert resp.status_code == 201

    resp = await app_client.post("/api/v1/plants", json=PLANT_DATA)
    assert resp.status_code == 201
    plant_id = resp.json()["data"]["id"]

    mock_client = AsyncMock()
    mock_client.generate = AsyncMock(side_effect=Exception("LLM down"))

    with (
        patch(
            "verdanta.services.plant_curation_service.create_llm_client",
            return_value=mock_client,
        ),
        patch(
            "verdanta.services.plant_curation_service.fetch_openfarm_crop",
            return_value=None,
        ),
    ):
        resp = await app_client.post(f"/api/v1/plants/{plant_id}/curate")

    assert resp.status_code == 502
    assert "Curation failed" in resp.json()["detail"]


async def test_recuration_replaces_old_sections(app_client: AsyncClient) -> None:
    """Test that re-curating replaces existing dossier sections."""
    resp = await app_client.post("/api/v1/gardens", json=GARDEN_DATA)
    assert resp.status_code == 201

    resp = await app_client.post("/api/v1/plants", json=PLANT_DATA)
    assert resp.status_code == 201
    plant_id = resp.json()["data"]["id"]

    mock_client = AsyncMock()
    mock_client.generate = AsyncMock(return_value=MOCK_LLM_RESPONSE)

    with (
        patch(
            "verdanta.services.plant_curation_service.create_llm_client",
            return_value=mock_client,
        ),
        patch(
            "verdanta.services.plant_curation_service.fetch_openfarm_crop",
            return_value=None,
        ),
    ):
        # Curate first time
        resp = await app_client.post(f"/api/v1/plants/{plant_id}/curate")
        assert resp.status_code == 200
        first_sections = resp.json()["data"]["dossier_sections"]

        # Curate second time
        resp = await app_client.post(f"/api/v1/plants/{plant_id}/curate")
        assert resp.status_code == 200
        second_sections = resp.json()["data"]["dossier_sections"]

    # Should still have 7 sections (replaced, not duplicated)
    assert len(second_sections) == 7

    # IDs should be different (new records)
    first_ids = {s["id"] for s in first_sections}
    second_ids = {s["id"] for s in second_sections}
    assert first_ids.isdisjoint(second_ids)

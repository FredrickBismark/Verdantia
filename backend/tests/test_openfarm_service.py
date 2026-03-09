"""Tests for OpenFarm service with mocked HTTP."""

from unittest.mock import AsyncMock, MagicMock, patch

from verdanta.services.openfarm_service import OpenFarmService


async def test_search_crops():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {
                "id": "tomato",
                "attributes": {
                    "name": "Tomato",
                    "binomial_name": "Solanum lycopersicum",
                    "sun_requirements": "Full Sun",
                },
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    db = AsyncMock()
    service = OpenFarmService(db)

    with patch("httpx.AsyncClient") as mock_http:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value = mock_instance

        results = await service.search_crops("tomato")
        assert len(results) == 1
        assert results[0]["attributes"]["name"] == "Tomato"


async def test_normalize_crop_data():
    db = AsyncMock()
    service = OpenFarmService(db)

    crop_data = {
        "id": "tomato",
        "attributes": {
            "name": "Tomato",
            "binomial_name": "Solanum lycopersicum",
            "description": "A popular garden vegetable",
            "sun_requirements": "Full Sun",
            "watering": "Moderate",
            "sowing_method": "Direct seed or transplant",
            "spread": 60,
            "row_spacing": 90,
            "height": 150,
            "growing_degree_days": 1200,
            "companions": ["basil", "carrot"],
            "tags_array": ["vegetable", "nightshade"],
            "main_image_path": "/img/tomato.jpg",
        },
    }

    normalized = service._normalize_crop_data(crop_data)
    assert normalized["common_name"] == "Tomato"
    assert normalized["scientific_name"] == "Solanum lycopersicum"
    assert normalized["sun_requirement"] == "Full Sun"
    assert normalized["companions"] == ["basil", "carrot"]
    assert normalized["slug"] == "tomato"


async def test_get_crop_not_found():
    mock_response = MagicMock()
    mock_response.status_code = 404

    db = AsyncMock()
    service = OpenFarmService(db)

    with patch("httpx.AsyncClient") as mock_http:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value = mock_instance

        result = await service.get_crop("nonexistent-plant")
        assert result is None

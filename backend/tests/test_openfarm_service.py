"""Tests for the OpenFarm service."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from verdanta.services.openfarm_service import (
    _extract_companions,
    _normalize_crop,
    fetch_openfarm_crop,
    search_openfarm,
)


def test_normalize_crop_basic() -> None:
    attrs = {
        "name": "Tomato",
        "binomial_name": "Solanum lycopersicum",
        "description": "A garden favorite",
        "sun_requirements": "Full Sun",
    }
    result = _normalize_crop("tomato-123", attrs)
    assert result["openfarm_id"] == "tomato-123"
    assert result["name"] == "Tomato"
    assert result["binomial_name"] == "Solanum lycopersicum"
    assert result["sun_requirements"] == "Full Sun"


def test_normalize_crop_empty() -> None:
    result = _normalize_crop("x", {})
    assert result["name"] == ""
    assert result["binomial_name"] is None


def test_extract_companions_with_data() -> None:
    attrs = {
        "companions": {
            "data": [
                {"attributes": {"name": "Basil"}},
                {"attributes": {"name": "Carrot"}},
            ]
        }
    }
    result = _extract_companions(attrs)
    assert result["companions"] == ["Basil", "Carrot"]
    assert result["antagonists"] == []


def test_extract_companions_empty() -> None:
    result = _extract_companions({})
    assert result["companions"] == []
    assert result["antagonists"] == []


async def test_search_openfarm_success() -> None:
    mock_response = {
        "data": [
            {
                "id": "tomato-1",
                "attributes": {
                    "name": "Tomato",
                    "binomial_name": "Solanum lycopersicum",
                },
            }
        ]
    }
    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response
    mock_resp.raise_for_status = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("verdanta.services.openfarm_service.httpx.AsyncClient", return_value=mock_client):
        results = await search_openfarm("Tomato")

    assert len(results) == 1
    assert results[0]["name"] == "Tomato"


async def test_search_openfarm_http_error() -> None:
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.HTTPError("timeout"))

    with patch("verdanta.services.openfarm_service.httpx.AsyncClient", return_value=mock_client):
        results = await search_openfarm("Tomato")

    assert results == []


async def test_fetch_openfarm_crop_exact_match() -> None:
    with patch(
        "verdanta.services.openfarm_service.search_openfarm",
        return_value=[
            {"name": "Cherry Tomato", "openfarm_id": "cherry"},
            {"name": "Tomato", "openfarm_id": "tomato"},
        ],
    ):
        result = await fetch_openfarm_crop("Tomato")

    assert result is not None
    assert result["openfarm_id"] == "tomato"


async def test_fetch_openfarm_crop_fallback() -> None:
    with patch(
        "verdanta.services.openfarm_service.search_openfarm",
        return_value=[{"name": "Cherry Tomato", "openfarm_id": "cherry"}],
    ):
        result = await fetch_openfarm_crop("Tomato")

    assert result is not None
    assert result["openfarm_id"] == "cherry"


async def test_fetch_openfarm_crop_not_found() -> None:
    with patch(
        "verdanta.services.openfarm_service.search_openfarm",
        return_value=[],
    ):
        result = await fetch_openfarm_crop("Nonexistent")

    assert result is None

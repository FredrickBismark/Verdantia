"""OpenFarm API client for plant data retrieval.

Queries https://openfarm.cc/api/v1/crops for plant information
and normalizes responses for the curation pipeline.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

OPENFARM_BASE = "https://openfarm.cc/api/v1"


async def search_openfarm(plant_name: str) -> list[dict]:
    """Search OpenFarm for crops matching the given name.

    Returns a list of normalized crop data dicts.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{OPENFARM_BASE}/crops",
                params={"filter": plant_name},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        logger.warning("OpenFarm API request failed for %r", plant_name)
        return []

    results: list[dict] = []
    for item in data.get("data", []):
        attrs = item.get("attributes", {})
        results.append(_normalize_crop(item.get("id", ""), attrs))
    return results


def _normalize_crop(crop_id: str, attrs: dict) -> dict:
    """Normalize OpenFarm crop attributes into a consistent structure."""
    return {
        "openfarm_id": crop_id,
        "name": attrs.get("name", ""),
        "binomial_name": attrs.get("binomial_name"),
        "description": attrs.get("description"),
        "sun_requirements": attrs.get("sun_requirements"),
        "sowing_method": attrs.get("sowing_method"),
        "spread": attrs.get("spread"),
        "row_spacing": attrs.get("row_spacing"),
        "height": attrs.get("height"),
        "growing_degree_days": attrs.get("growing_degree_days"),
        "tags_array": attrs.get("tags_array", []),
        "main_image_path": attrs.get("main_image_path"),
        "companions": _extract_companions(attrs),
    }


def _extract_companions(attrs: dict) -> dict:
    """Extract companion/antagonist plant lists from OpenFarm data."""
    companions: list[str] = []
    antagonists: list[str] = []
    for comp in attrs.get("companions", {}).get("data", []):
        name = comp.get("attributes", {}).get("name")
        if name:
            companions.append(name)
    return {"companions": companions, "antagonists": antagonists}


async def fetch_openfarm_crop(plant_name: str) -> dict | None:
    """Fetch the best-matching crop from OpenFarm.

    Returns normalized crop data or None if not found.
    """
    results = await search_openfarm(plant_name)
    if not results:
        return None

    # Prefer exact name match (case-insensitive)
    name_lower = plant_name.lower()
    for crop in results:
        if crop["name"].lower() == name_lower:
            return crop

    # Fall back to first result
    return results[0]

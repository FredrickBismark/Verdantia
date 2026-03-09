"""OpenFarm API client for plant data retrieval.

Queries https://openfarm.cc/api/v1/crops for plant information
and normalizes responses for the curation pipeline.
"""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.models.plant import PlantDataSource, PlantSpecies

OPENFARM_API_BASE = "https://openfarm.cc/api/v1"


class OpenFarmService:
    """Fetches plant data from OpenFarm and stores as PlantDataSource records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search_crops(self, query: str) -> list[dict]:
        """Search OpenFarm for crops matching query string."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{OPENFARM_API_BASE}/crops",
                params={"filter": query},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])

    async def get_crop(self, slug: str) -> dict | None:
        """Get a single crop by slug from OpenFarm."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{OPENFARM_API_BASE}/crops/{slug}")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json().get("data")

    def _normalize_crop_data(self, crop_data: dict) -> dict:
        """Extract and normalize relevant fields from OpenFarm crop data."""
        attrs = crop_data.get("attributes", {})
        return {
            "common_name": attrs.get("name", ""),
            "scientific_name": attrs.get("binomial_name"),
            "description": attrs.get("description"),
            "sun_requirement": attrs.get("sun_requirements"),
            "water_requirement": attrs.get("watering"),
            "sowing_method": attrs.get("sowing_method"),
            "spread": attrs.get("spread"),
            "row_spacing": attrs.get("row_spacing"),
            "height": attrs.get("height"),
            "growing_degree_days": attrs.get("growing_degree_days"),
            "companions": attrs.get("companions", []),
            "tags": attrs.get("tags_array", []),
            "main_image_path": attrs.get("main_image_path"),
            "slug": crop_data.get("id"),
        }

    async def ingest_for_species(self, species: PlantSpecies) -> PlantDataSource | None:
        """Search OpenFarm for matching crop data and store as a data source.

        Returns the created PlantDataSource or None if no match found.
        """
        results = await self.search_crops(species.common_name)
        if not results:
            return None

        # Use the first (best) match
        crop_data = results[0]
        normalized = self._normalize_crop_data(crop_data)

        # Check if we already have this source
        from sqlalchemy import select

        existing = await self.db.execute(
            select(PlantDataSource).where(
                PlantDataSource.species_id == species.id,
                PlantDataSource.source_type == "openfarm",
            )
        )
        if existing.scalar_one_or_none():
            return None

        source = PlantDataSource(
            species_id=species.id,
            source_type="openfarm",
            source_name="OpenFarm",
            source_url=f"https://openfarm.cc/en/crops/{crop_data.get('id', '')}",
            raw_data=normalized,
            confidence_score=0.7,
            notes=f"Auto-ingested from OpenFarm search for '{species.common_name}'",
        )
        self.db.add(source)
        await self.db.flush()
        await self.db.refresh(source)
        return source

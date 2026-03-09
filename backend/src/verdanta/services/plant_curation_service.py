"""Plant curation pipeline — the intelligence engine for building plant dossiers.

Gathers raw data from multiple sources, sends to LLM for synthesis,
and stores structured dossier sections with confidence levels.
"""

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.models.plant import DossierSection, PlantDataSource, PlantSpecies
from verdanta.services.llm_service import LLMService
from verdanta.services.openfarm_service import OpenFarmService

DOSSIER_SECTIONS = [
    ("overview", "Overview"),
    ("growing_conditions", "Growing Conditions"),
    ("planting_guide", "Planting Guide"),
    ("care_maintenance", "Care & Maintenance"),
    ("pests_diseases", "Pests & Diseases"),
    ("harvesting", "Harvesting"),
    ("companion_planting", "Companion Planting"),
]

CURATION_SYSTEM_PROMPT = """\
You are a horticultural expert assistant. Given plant data from
various sources, synthesize accurate, practical dossier sections
for gardeners.

For each section, assess confidence as:
- "high": Well-supported by multiple sources or widely accepted knowledge
- "medium": Supported by one source or generally accepted but varies by region
- "low": Limited data, anecdotal, or uncertain

Respond in JSON format with this structure:
{
  "sections": [
    {
      "section_type": "overview",
      "title": "Overview",
      "content": "...",
      "confidence": "high|medium|low"
    }
  ],
  "enriched_data": {
    "days_to_maturity_min": null,
    "days_to_maturity_max": null,
    "sun_requirement": null,
    "water_requirement": null,
    "frost_tolerance": null,
    "spacing_cm": null,
    "depth_cm": null,
    "companion_plants": {},
    "antagonist_plants": {}
  }
}

Only include enriched_data fields that you have high confidence in.
Omit or set to null any fields you're unsure about."""


class PlantCurationService:
    """Orchestrates the plant curation pipeline."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.llm_service = LLMService(db)
        self.openfarm_service = OpenFarmService(db)

    async def curate_species(self, species_id: int) -> PlantSpecies:
        """Run the full curation pipeline for a plant species.

        1. Gather data from OpenFarm (and other sources in future)
        2. Assemble context from all data sources
        3. Send to LLM for synthesis
        4. Store dossier sections
        5. Update species with enriched data
        """
        species = await self.db.get(PlantSpecies, species_id)
        if not species:
            raise ValueError(f"PlantSpecies {species_id} not found")

        # Update status to in-progress
        species.curation_status = "curating"
        await self.db.flush()

        try:
            # Step 1: Gather external data
            await self.openfarm_service.ingest_for_species(species)

            # Step 2: Load all data sources
            result = await self.db.execute(
                select(PlantDataSource).where(PlantDataSource.species_id == species_id)
            )
            sources = result.scalars().all()

            # Step 3: Build prompt
            prompt = self._build_curation_prompt(species, sources)

            # Step 4: Call LLM
            llm_response = await self.llm_service.generate(
                prompt=prompt,
                system=CURATION_SYSTEM_PROMPT,
                interaction_type="curation",
                response_format="json",
            )

            # Step 5: Parse and store results
            parsed = json.loads(llm_response.text)
            await self._store_dossier_sections(species, parsed, sources)
            self._apply_enriched_data(species, parsed)

            # Mark complete
            species.curation_status = "curated"
            species.last_curated_at = datetime.now(UTC)
            species.curation_model = llm_response.model
            await self.db.flush()
            await self.db.refresh(species)

        except Exception:
            species.curation_status = "error"
            await self.db.flush()
            raise

        return species

    def _build_curation_prompt(
        self, species: PlantSpecies, sources: list[PlantDataSource]
    ) -> str:
        """Assemble a context-rich prompt from species data and all sources."""
        parts = [
            f"Plant: {species.common_name}",
        ]
        if species.scientific_name:
            parts.append(f"Scientific name: {species.scientific_name}")
        if species.family:
            parts.append(f"Family: {species.family}")
        if species.variety:
            parts.append(f"Variety: {species.variety}")
        if species.growth_habit:
            parts.append(f"Growth habit: {species.growth_habit}")

        parts.append("")
        parts.append("=== DATA SOURCES ===")
        for source in sources:
            parts.append(f"\n--- {source.source_name} ({source.source_type}) ---")
            parts.append(f"Confidence: {source.confidence_score or 'unknown'}")
            parts.append(json.dumps(source.raw_data, indent=2, default=str))

        parts.append("")
        parts.append("=== REQUESTED SECTIONS ===")
        for section_type, title in DOSSIER_SECTIONS:
            parts.append(f"- {section_type}: {title}")

        parts.append("")
        parts.append(
            "Please synthesize the above data into comprehensive dossier sections "
            "and extract any structured enriched_data fields you're confident about."
        )

        return "\n".join(parts)

    async def _store_dossier_sections(
        self,
        species: PlantSpecies,
        parsed: dict,
        sources: list[PlantDataSource],
    ) -> None:
        """Delete old sections and store new ones from LLM output."""
        # Remove existing sections
        result = await self.db.execute(
            select(DossierSection).where(DossierSection.species_id == species.id)
        )
        for old in result.scalars().all():
            await self.db.delete(old)

        source_ids = [s.id for s in sources]
        for i, section_data in enumerate(parsed.get("sections", [])):
            section = DossierSection(
                species_id=species.id,
                section_type=section_data.get("section_type", f"section_{i}"),
                title=section_data.get("title", f"Section {i + 1}"),
                content=section_data.get("content", ""),
                confidence=section_data.get("confidence", "medium"),
                source_ids=source_ids,
                display_order=i,
                is_localized=False,
            )
            self.db.add(section)
        await self.db.flush()

    def _apply_enriched_data(self, species: PlantSpecies, parsed: dict) -> None:
        """Apply LLM-extracted structured data to the species model."""
        enriched = parsed.get("enriched_data", {})
        if not enriched:
            return

        field_mapping = {
            "days_to_maturity_min": "days_to_maturity_min",
            "days_to_maturity_max": "days_to_maturity_max",
            "sun_requirement": "sun_requirement",
            "water_requirement": "water_requirement",
            "frost_tolerance": "frost_tolerance",
            "spacing_cm": "spacing_cm",
            "depth_cm": "depth_cm",
            "companion_plants": "companion_plants",
            "antagonist_plants": "antagonist_plants",
        }

        for json_key, model_attr in field_mapping.items():
            value = enriched.get(json_key)
            if value is not None:
                setattr(species, model_attr, value)

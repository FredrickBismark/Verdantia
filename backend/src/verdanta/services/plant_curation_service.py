"""Plant curation pipeline — the intelligence engine for building plant dossiers.

Gathers raw data from multiple sources, sends to LLM for synthesis,
and stores structured dossier sections with confidence levels.
"""

import json
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.models.plant import DossierSection, PlantDataSource, PlantSpecies
from verdanta.models.settings import AppSettings
from verdanta.services.llm_service import (
    LLMConfig,
    create_llm_client,
    get_llm_config_from_settings,
)
from verdanta.services.openfarm_service import fetch_openfarm_crop

logger = logging.getLogger(__name__)

DOSSIER_SECTIONS = [
    ("overview", "Overview"),
    ("growing_conditions", "Growing Conditions"),
    ("planting_guide", "Planting Guide"),
    ("care_maintenance", "Care & Maintenance"),
    ("harvest_storage", "Harvest & Storage"),
    ("pests_diseases", "Pests & Diseases"),
    ("companion_planting", "Companion Planting"),
]

CURATION_SYSTEM_PROMPT = """\
You are a horticultural expert AI. You will be given raw data about a plant \
species from various sources. Synthesize this information into a structured \
plant dossier.

Return a JSON object with exactly these keys, each containing a sub-object \
with "content" (string, 2-4 paragraphs of practical gardening advice) and \
"confidence" (one of "high", "medium", "low"):

{
  "overview": {"content": "...", "confidence": "high"},
  "growing_conditions": {"content": "...", "confidence": "..."},
  "planting_guide": {"content": "...", "confidence": "..."},
  "care_maintenance": {"content": "...", "confidence": "..."},
  "harvest_storage": {"content": "...", "confidence": "..."},
  "pests_diseases": {"content": "...", "confidence": "..."},
  "companion_planting": {"content": "...", "confidence": "..."}
}

Guidelines:
- Base confidence on how well-supported the information is across sources.
- Use "high" when multiple sources agree, "medium" for single-source info, \
"low" for inferred/uncertain information.
- Write practical, actionable content for home gardeners.
- If data is contradictory, note the disagreement and use your best judgment.
- Return ONLY valid JSON, no markdown fences or extra text.\
"""


async def _load_settings(db: AsyncSession) -> dict[str, str]:
    """Load all app settings as a dict."""
    result = await db.execute(select(AppSettings))
    return {s.key: s.value for s in result.scalars().all()}


async def _gather_openfarm_data(plant: PlantSpecies, db: AsyncSession) -> PlantDataSource | None:
    """Fetch data from OpenFarm and store as a PlantDataSource."""
    crop = await fetch_openfarm_crop(plant.common_name)
    if not crop:
        return None

    source = PlantDataSource(
        species_id=plant.id,
        source_type="openfarm",
        source_name="OpenFarm",
        source_url=f"https://openfarm.cc/crops/{crop.get('openfarm_id', '')}",
        raw_data=crop,
        confidence_score=0.7,
        notes="Auto-fetched during curation",
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


def _build_plant_context(plant: PlantSpecies) -> str:
    """Build a summary of known plant attributes for the LLM prompt."""
    fields = {
        "Common Name": plant.common_name,
        "Scientific Name": plant.scientific_name,
        "Family": plant.family,
        "Variety": plant.variety,
        "Growth Habit": plant.growth_habit,
        "Days to Maturity": (
            f"{plant.days_to_maturity_min}-{plant.days_to_maturity_max}"
            if plant.days_to_maturity_min and plant.days_to_maturity_max
            else None
        ),
        "Sun Requirement": plant.sun_requirement,
        "Water Requirement": plant.water_requirement,
        "Frost Tolerance": plant.frost_tolerance,
        "Spacing (cm)": plant.spacing_cm,
        "Planting Depth (cm)": plant.depth_cm,
    }
    lines = [f"- {k}: {v}" for k, v in fields.items() if v]
    return "Known plant attributes:\n" + "\n".join(lines)


def _build_curation_prompt(
    plant: PlantSpecies,
    sources: list[PlantDataSource],
) -> str:
    """Assemble the full curation prompt from plant data and raw sources."""
    parts = [_build_plant_context(plant), ""]

    for i, source in enumerate(sources, 1):
        parts.append(f"--- Source {i}: {source.source_name} ({source.source_type}) ---")
        raw = source.raw_data
        if isinstance(raw, dict):
            parts.append(json.dumps(raw, indent=2, default=str)[:3000])
        else:
            parts.append(str(raw)[:3000])
        parts.append("")

    if not sources:
        parts.append(
            "No external sources available. Use your knowledge base to generate "
            "the dossier, but mark confidence as 'low' for all sections."
        )

    parts.append("\nSynthesize the above into a plant dossier. Return ONLY valid JSON.")
    return "\n".join(parts)


def _parse_dossier_response(
    text: str,
) -> dict[str, dict[str, str]]:
    """Parse the LLM response into section data."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [line for line in lines if not line.startswith("```")]
        cleaned = "\n".join(lines)

    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    return data


async def curate_plant(plant_id: int, db: AsyncSession) -> PlantSpecies:
    """Run the full curation pipeline for a plant species.

    1. Gather data from OpenFarm (and existing sources)
    2. Send to LLM for synthesis
    3. Store dossier sections
    4. Update plant curation status
    """
    plant = await db.get(PlantSpecies, plant_id)
    if not plant:
        raise ValueError(f"Plant {plant_id} not found")

    # Load LLM config from settings
    settings = await _load_settings(db)
    llm_config: LLMConfig = await get_llm_config_from_settings(settings)
    llm_client = create_llm_client(llm_config)

    # Gather sources
    sources: list[PlantDataSource] = []

    # Fetch from OpenFarm
    openfarm_source = await _gather_openfarm_data(plant, db)
    if openfarm_source:
        sources.append(openfarm_source)

    # Include any existing data sources
    result = await db.execute(select(PlantDataSource).where(PlantDataSource.species_id == plant_id))
    existing = result.scalars().all()
    for src in existing:
        if src.id not in [s.id for s in sources]:
            sources.append(src)

    # Build prompt and call LLM
    prompt = _build_curation_prompt(plant, sources)
    llm_response = await llm_client.generate(
        prompt=prompt,
        system=CURATION_SYSTEM_PROMPT,
        response_format="json",
    )

    # Parse response and create dossier sections
    dossier_data = _parse_dossier_response(llm_response.text)

    # Remove old dossier sections
    old_sections = await db.execute(
        select(DossierSection).where(DossierSection.species_id == plant_id)
    )
    for old in old_sections.scalars().all():
        await db.delete(old)

    # Create new sections
    source_ids = [s.id for s in sources]
    for order, (section_type, title) in enumerate(DOSSIER_SECTIONS):
        section_data = dossier_data.get(section_type, {})
        if not section_data:
            continue
        section = DossierSection(
            species_id=plant_id,
            section_type=section_type,
            title=title,
            content=section_data.get("content", ""),
            confidence=section_data.get("confidence", "low"),
            source_ids=source_ids,
            display_order=order,
            is_localized=False,
            last_updated=datetime.now(UTC),
        )
        db.add(section)

    # Update plant curation status
    plant.curation_status = "curated"
    plant.last_curated_at = datetime.now(UTC)
    plant.curation_model = llm_response.model

    # Log the LLM interaction
    from verdanta.models.llm import LLMInteraction

    interaction = LLMInteraction(
        garden_id=None,  # Curation is not garden-specific
        interaction_type="plant_curation",
        user_prompt=prompt[:5000],
        system_context=CURATION_SYSTEM_PROMPT,
        response=llm_response.text[:5000],
        model_used=llm_response.model,
        provider=llm_response.provider,
        status="completed",
        duration_ms=llm_response.duration_ms,
        tokens_used=llm_response.tokens_used,
    )
    db.add(interaction)

    await db.flush()
    await db.refresh(plant)
    return plant

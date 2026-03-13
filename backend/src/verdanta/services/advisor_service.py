"""Garden advisor service — LLM-powered chat with contextual garden awareness.

Assembles context from garden, active plantings, recent weather, and species
dossiers before sending to the configured LLM. Logs every interaction.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.models.garden import Garden
from verdanta.models.llm import LLMInteraction
from verdanta.models.plant import DossierSection, PlantSpecies
from verdanta.models.planting import Planting
from verdanta.models.settings import AppSettings
from verdanta.models.weather import WeatherRecord
from verdanta.schemas.advisor import ChatResponse
from verdanta.services.llm_service import create_llm_client, get_llm_config_from_settings

logger = logging.getLogger(__name__)

ADVISOR_SYSTEM_PROMPT = """\
You are Verdanta, an expert garden advisor with deep knowledge of horticulture, \
plant care, and local growing conditions. You have been given context about the \
user's garden, active plantings, and recent weather. Use this context to give \
specific, actionable advice tailored to their situation.

Guidelines:
- Be concise and practical — focus on what the gardener should actually do.
- Reference specific plants, weather conditions, or dates when relevant.
- If you are uncertain, say so rather than guessing.
- Suggest when to seek additional data (soil tests, pest identification, etc.).
- Keep responses conversational but informative.
"""


class AdvisorService:
    """Handles chat interactions with context assembly and LLM routing."""

    async def chat(
        self,
        message: str,
        garden: Garden,
        db: AsyncSession,
        planting_id: int | None = None,
    ) -> ChatResponse:
        """Assemble garden context, query the LLM, log the interaction."""
        context = await self._assemble_context(garden, db, planting_id)
        db_settings = await _load_settings(db)
        config = await get_llm_config_from_settings(db_settings)
        client = create_llm_client(config)

        full_system = f"{ADVISOR_SYSTEM_PROMPT}\n\n{context}"

        llm_response = await client.generate(
            prompt=message,
            system=full_system,
        )

        interaction = LLMInteraction(
            garden_id=garden.id,
            planting_id=planting_id,
            interaction_type="advisor_chat",
            user_prompt=message,
            system_context=context,
            response=llm_response.text,
            model_used=llm_response.model,
            provider=llm_response.provider,
            status="completed",
            duration_ms=llm_response.duration_ms,
            tokens_used=llm_response.tokens_used,
            timestamp=datetime.now(UTC),
        )
        db.add(interaction)
        await db.flush()
        await db.refresh(interaction)

        return ChatResponse(
            response=llm_response.text,
            model_used=llm_response.model,
            provider=llm_response.provider,
            context_summary=_summarize_context(garden, context),
            interaction_id=interaction.id,
        )

    async def _assemble_context(
        self,
        garden: Garden,
        db: AsyncSession,
        planting_id: int | None = None,
    ) -> str:
        """Build a text context block to inject into the system prompt."""
        parts: list[str] = []

        # Garden overview
        parts.append(
            f"## Garden: {garden.name}\n"
            f"- Location: {garden.latitude:.4f}°, {garden.longitude:.4f}°\n"
            f"- Timezone: {garden.timezone}\n"
            f"- USDA Zone: {garden.usda_zone or 'unknown'}\n"
            f"- Soil type: {garden.soil_type_default or 'unknown'}\n"
        )

        # Active plantings
        result = await db.execute(
            select(Planting, PlantSpecies)
            .join(PlantSpecies, Planting.species_id == PlantSpecies.id)
            .where(Planting.garden_id == garden.id)
            .where(Planting.date_removed.is_(None))
            .limit(10)
        )
        rows = result.all()
        if rows:
            parts.append("\n## Active Plantings")
            for planting, species in rows:
                indicator = " ← FOCUS" if planting_id and planting.id == planting_id else ""
                parts.append(
                    f"- {species.common_name}{indicator} "
                    f"(planted: {planting.date_seeded or planting.date_transplanted or 'unknown'}, "
                    f"status: {planting.status}, "
                    f"bed: {planting.bed_or_location or 'unspecified'})"
                )

        # If a specific planting is focused, include species details
        if planting_id:
            focused_planting = await db.get(Planting, planting_id)
            if focused_planting:
                species = await db.get(PlantSpecies, focused_planting.species_id)
                if species:
                    parts.append(f"\n## Focused Plant: {species.common_name}")
                    if species.days_to_maturity_min:
                        maturity = str(species.days_to_maturity_min)
                        if species.days_to_maturity_max:
                            maturity += f"–{species.days_to_maturity_max}"
                        parts.append(f"- Days to maturity: {maturity}")
                    if species.sun_requirement:
                        parts.append(f"- Sun: {species.sun_requirement}")
                    if species.water_requirement:
                        parts.append(f"- Water: {species.water_requirement}")
                    if species.frost_tolerance:
                        parts.append(f"- Frost tolerance: {species.frost_tolerance}")

                    # Include curated dossier sections if available —
                    # limited to the most actionable sections to keep context compact.
                    if species.curation_status == "curated":
                        dossier_result = await db.execute(
                            select(DossierSection)
                            .where(DossierSection.species_id == species.id)
                            .where(
                                DossierSection.section_type.in_(
                                    [
                                        "overview",
                                        "care_maintenance",
                                        "pests_diseases",
                                    ]
                                )
                            )
                            .order_by(DossierSection.display_order)
                        )
                        sections = dossier_result.scalars().all()
                        if sections:
                            parts.append(f"\n### Curated Knowledge: {species.common_name}")
                            for section in sections:
                                parts.append(
                                    f"\n**{section.title}** "
                                    f"(confidence: {section.confidence}):\n"
                                    + section.content[:600]
                                )

        # Recent weather (last 3 records)
        weather_result = await db.execute(
            select(WeatherRecord)
            .where(WeatherRecord.garden_id == garden.id)
            .where(WeatherRecord.record_type.in_(["current", "forecast"]))
            .order_by(WeatherRecord.fetched_at.desc())
            .limit(5)
        )
        weather_records = weather_result.scalars().all()
        if weather_records:
            parts.append("\n## Recent & Forecast Weather")
            for rec in weather_records:
                temp_str = (
                    f"temp {rec.temp_c:.1f}°C" if rec.temp_c is not None else "no temp data"
                )
                frost_note = " ⚠ FROST RISK" if rec.frost_risk else ""
                parts.append(
                    f"- {rec.timestamp.date()} ({rec.record_type}): "
                    f"{temp_str}{frost_note}"
                )

        parts.append(f"\n## Today's Date\n{datetime.now(UTC).date()}")
        return "\n".join(parts)


async def _load_settings(db: AsyncSession) -> dict[str, str]:
    result = await db.execute(select(AppSettings))
    return {s.key: s.value for s in result.scalars().all()}


def _summarize_context(garden: Garden, context: str) -> str:
    """Return a brief description of what context was assembled."""
    lines = context.strip().split("\n")
    return f"Garden '{garden.name}' — {len(lines)} context lines assembled"

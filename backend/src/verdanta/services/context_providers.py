"""Context provider protocol and concrete implementations.

Each provider extracts a specific type of context from the database
and returns it as ContextChunks for the advisor to include in prompts.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.models.journal import JournalEntry
from verdanta.models.plant import DossierSection, PlantSpecies
from verdanta.models.planting import CalendarEvent, Planting
from verdanta.models.weather import WeatherRecord

logger = logging.getLogger(__name__)


@dataclass
class ContextChunk:
    source: str
    content: str
    relevance: float
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class ContextProvider(Protocol):
    """Interface for providing context chunks to the advisor."""

    provider_name: str

    async def get_context(
        self,
        garden_id: int,
        db: AsyncSession,
        planting_id: int | None = None,
        query: str | None = None,
        max_tokens: int = 2000,
    ) -> list[ContextChunk]: ...


class PlantingContextProvider:
    """Provides context about active plantings and focused species."""

    provider_name = "plantings"

    async def get_context(
        self,
        garden_id: int,
        db: AsyncSession,
        planting_id: int | None = None,
        query: str | None = None,
        max_tokens: int = 2000,
    ) -> list[ContextChunk]:
        chunks: list[ContextChunk] = []

        result = await db.execute(
            select(Planting, PlantSpecies)
            .join(PlantSpecies, Planting.species_id == PlantSpecies.id)
            .where(Planting.garden_id == garden_id)
            .where(Planting.date_removed.is_(None))
            .limit(10)
        )
        rows = result.all()
        if not rows:
            return chunks

        lines = ["## Active Plantings"]
        for planting, species in rows:
            indicator = " ← FOCUS" if planting_id and planting.id == planting_id else ""
            lines.append(
                f"- {species.common_name}{indicator} "
                f"(planted: {planting.date_seeded or planting.date_transplanted or 'unknown'}, "
                f"status: {planting.status}, "
                f"bed: {planting.bed_or_location or 'unspecified'})"
            )
        chunks.append(ContextChunk(
            source="plantings",
            content="\n".join(lines),
            relevance=0.9,
            metadata={"count": len(rows)},
        ))

        # Focused planting species details
        if planting_id:
            focused = await db.get(Planting, planting_id)
            if focused:
                species = await db.get(PlantSpecies, focused.species_id)
                if species:
                    details = [f"\n## Focused Plant: {species.common_name}"]
                    if species.days_to_maturity_min:
                        mat = str(species.days_to_maturity_min)
                        if species.days_to_maturity_max:
                            mat += f"–{species.days_to_maturity_max}"
                        details.append(f"- Days to maturity: {mat}")
                    if species.sun_requirement:
                        details.append(f"- Sun: {species.sun_requirement}")
                    if species.water_requirement:
                        details.append(f"- Water: {species.water_requirement}")
                    if species.frost_tolerance:
                        details.append(f"- Frost tolerance: {species.frost_tolerance}")
                    chunks.append(ContextChunk(
                        source="planting_focus",
                        content="\n".join(details),
                        relevance=1.0,
                        metadata={"species_id": species.id},
                    ))

        return chunks


class WeatherContextProvider:
    """Provides recent weather conditions and forecast summary."""

    provider_name = "weather"

    async def get_context(
        self,
        garden_id: int,
        db: AsyncSession,
        planting_id: int | None = None,
        query: str | None = None,
        max_tokens: int = 2000,
    ) -> list[ContextChunk]:
        result = await db.execute(
            select(WeatherRecord)
            .where(WeatherRecord.garden_id == garden_id)
            .where(WeatherRecord.record_type.in_(["current", "forecast"]))
            .order_by(WeatherRecord.fetched_at.desc())
            .limit(5)
        )
        records = result.scalars().all()
        if not records:
            return []

        lines = ["## Recent & Forecast Weather"]
        for rec in records:
            temp_str = f"temp {rec.temp_c:.1f}°C" if rec.temp_c is not None else "no temp data"
            frost_note = " ⚠ FROST RISK" if rec.frost_risk else ""
            lines.append(
                f"- {rec.timestamp.date()} ({rec.record_type}): "
                f"{temp_str}{frost_note}"
            )
        return [ContextChunk(
            source="weather",
            content="\n".join(lines),
            relevance=0.7,
            metadata={"records": len(records)},
        )]


class DossierContextProvider:
    """Provides relevant dossier sections for focused plants."""

    provider_name = "dossier"

    async def get_context(
        self,
        garden_id: int,
        db: AsyncSession,
        planting_id: int | None = None,
        query: str | None = None,
        max_tokens: int = 2000,
    ) -> list[ContextChunk]:
        if not planting_id:
            return []

        focused = await db.get(Planting, planting_id)
        if not focused:
            return []

        species = await db.get(PlantSpecies, focused.species_id)
        if not species or species.curation_status != "curated":
            return []

        result = await db.execute(
            select(DossierSection)
            .where(DossierSection.species_id == species.id)
            .where(
                DossierSection.section_type.in_(
                    ["overview", "care_maintenance", "pests_diseases"]
                )
            )
            .order_by(DossierSection.display_order)
        )
        sections = result.scalars().all()
        if not sections:
            return []

        lines = [f"\n### Curated Knowledge: {species.common_name}"]
        for section in sections:
            lines.append(
                f"\n**{section.title}** (confidence: {section.confidence}):\n"
                + section.content[:600]
            )
        return [ContextChunk(
            source="dossier",
            content="\n".join(lines),
            relevance=0.8,
            metadata={"species_id": species.id},
        )]


class JournalContextProvider:
    """Provides recent journal entries for the garden/planting."""

    provider_name = "journal"

    async def get_context(
        self,
        garden_id: int,
        db: AsyncSession,
        planting_id: int | None = None,
        query: str | None = None,
        max_tokens: int = 2000,
    ) -> list[ContextChunk]:
        q = (
            select(JournalEntry)
            .where(JournalEntry.garden_id == garden_id)
            .order_by(JournalEntry.entry_date.desc())
            .limit(5)
        )
        if planting_id:
            q = q.where(
                (JournalEntry.planting_id == planting_id)
                | (JournalEntry.planting_id.is_(None))
            )

        result = await db.execute(q)
        entries = result.scalars().all()
        if not entries:
            return []

        lines = ["## Recent Journal Entries"]
        for entry in entries:
            lines.append(
                f"- [{entry.entry_date}] ({entry.category}) {entry.content[:200]}"
            )
        return [ContextChunk(
            source="journal",
            content="\n".join(lines),
            relevance=0.6,
            metadata={"count": len(entries)},
        )]


class CalendarContextProvider:
    """Provides upcoming calendar events."""

    provider_name = "calendar"

    async def get_context(
        self,
        garden_id: int,
        db: AsyncSession,
        planting_id: int | None = None,
        query: str | None = None,
        max_tokens: int = 2000,
    ) -> list[ContextChunk]:
        today = datetime.now(UTC).date()
        q = (
            select(CalendarEvent)
            .where(CalendarEvent.garden_id == garden_id)
            .where(CalendarEvent.completed.is_(False))
            .where(CalendarEvent.scheduled_date >= today)
            .order_by(CalendarEvent.scheduled_date)
            .limit(10)
        )
        result = await db.execute(q)
        events = result.scalars().all()
        if not events:
            return []

        lines = ["## Upcoming Tasks"]
        for evt in events:
            lines.append(
                f"- [{evt.scheduled_date}] {evt.title} ({evt.event_type})"
            )
        return [ContextChunk(
            source="calendar",
            content="\n".join(lines),
            relevance=0.5,
            metadata={"count": len(events)},
        )]


def get_default_providers() -> list[ContextProvider]:
    """Return the default set of context providers."""
    return [
        PlantingContextProvider(),
        WeatherContextProvider(),
        DossierContextProvider(),
        JournalContextProvider(),
        CalendarContextProvider(),
    ]

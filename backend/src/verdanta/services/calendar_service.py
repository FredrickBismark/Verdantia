"""Calendar and scheduling service.

Auto-generates planting schedules from species data and frost dates.
Uses species cultivation metadata (days_to_maturity, frost_tolerance, etc.)
to create a sequence of care events for a planting.
"""

import logging
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.models.garden import Garden
from verdanta.models.plant import PlantSpecies
from verdanta.models.planting import CalendarEvent, Planting
from verdanta.services.weather_service import WeatherService

logger = logging.getLogger(__name__)

# Event type colour palette for UI
_EVENT_COLORS: dict[str, str] = {
    "seed_indoors": "#8B5CF6",   # purple
    "transplant": "#F59E0B",      # amber
    "direct_sow": "#10B981",      # green
    "fertilize": "#3B82F6",       # blue
    "water": "#06B6D4",           # cyan
    "harvest": "#EF4444",         # red
    "prune": "#F97316",           # orange
    "pest_check": "#6366F1",      # indigo
    "remove": "#6B7280",          # grey
    "frost_alert": "#EC4899",     # pink
}

# Default event offsets relative to transplant/direct-sow date (in days)
_FROST_SENSITIVE = {"tender", "frost sensitive", "none", "no frost tolerance"}
_FROST_HARDY = {"very hardy", "hardy", "semi-hardy"}

# Weeks before last spring frost to start seeds indoors
_WEEKS_INDOORS = 6

# Care schedule after transplant (offset in days, event_type, title)
_CARE_SCHEDULE: list[tuple[int, str, str]] = [
    (7, "fertilize", "Fertilize — establishment feed"),
    (14, "pest_check", "Pest & disease check"),
    (30, "fertilize", "Fertilize — mid-season"),
    (45, "pest_check", "Pest & disease check"),
]


class CalendarService:
    """Generates and manages calendar events for plantings."""

    def __init__(self) -> None:
        self._weather_svc = WeatherService()

    async def generate_schedule(
        self,
        planting: Planting,
        species: PlantSpecies,
        garden: Garden,
        db: AsyncSession,
    ) -> list[CalendarEvent]:
        """Generate a full care schedule for a planting.

        Logic:
        1. Determine sow/transplant anchor date from frost data or planting dates.
        2. Create seed-indoors event (if frost-sensitive and no direct-sow date).
        3. Create transplant or direct-sow event.
        4. Create harvest window events based on days_to_maturity.
        5. Create periodic care events (fertilize, pest checks).
        6. Create end-of-season removal event.
        """
        frost_data = await self._weather_svc.estimate_frost_dates(garden.id, db)
        last_spring_frost = _parse_date(frost_data.get("last_spring_frost"))
        first_fall_frost = _parse_date(frost_data.get("first_fall_frost"))

        frost_tolerance = (species.frost_tolerance or "").lower()
        is_frost_sensitive = frost_tolerance in _FROST_SENSITIVE or frost_tolerance == ""

        # Determine anchor: prefer recorded dates, otherwise estimate from frost
        anchor = _determine_anchor(planting, species, last_spring_frost, is_frost_sensitive)

        events: list[CalendarEvent] = []

        # Seed indoors (frost-sensitive species only, 6 weeks before transplant)
        if is_frost_sensitive and planting.date_seeded is None and anchor is not None:
            seed_date = anchor - timedelta(weeks=_WEEKS_INDOORS)
            if seed_date > date.today() or planting.date_seeded is None:
                events.append(
                    _make_event(
                        garden_id=garden.id,
                        planting_id=planting.id,
                        event_type="seed_indoors",
                        title=f"Start {species.common_name} seeds indoors",
                        description=(
                            f"Sow seeds {_WEEKS_INDOORS} weeks before last frost "
                            f"({last_spring_frost}) in trays."
                        ),
                        scheduled_date=seed_date,
                        source="auto",
                        priority="high",
                        weather_dependent=False,
                        color=_EVENT_COLORS["seed_indoors"],
                    )
                )

        # Transplant or direct sow
        if anchor is not None:
            if is_frost_sensitive:
                events.append(
                    _make_event(
                        garden_id=garden.id,
                        planting_id=planting.id,
                        event_type="transplant",
                        title=f"Transplant {species.common_name}",
                        description=(
                            "Harden off for 7 days before transplanting "
                            "outdoors after last frost."
                        ),
                        scheduled_date=anchor,
                        source="auto",
                        priority="high",
                        weather_dependent=True,
                        color=_EVENT_COLORS["transplant"],
                    )
                )
            else:
                events.append(
                    _make_event(
                        garden_id=garden.id,
                        planting_id=planting.id,
                        event_type="direct_sow",
                        title=f"Direct sow {species.common_name}",
                        description="Sow directly into prepared bed.",
                        scheduled_date=anchor,
                        source="auto",
                        priority="high",
                        weather_dependent=False,
                        color=_EVENT_COLORS["direct_sow"],
                    )
                )

        # Harvest window
        if anchor is not None and species.days_to_maturity_min is not None:
            harvest_start = anchor + timedelta(days=species.days_to_maturity_min)
            events.append(
                _make_event(
                    garden_id=garden.id,
                    planting_id=planting.id,
                    event_type="harvest",
                    title=f"First harvest — {species.common_name}",
                    description=(
                        f"Expected first harvest "
                        f"({species.days_to_maturity_min} days from sow)."
                    ),
                    scheduled_date=harvest_start,
                    source="auto",
                    priority="medium",
                    weather_dependent=False,
                    color=_EVENT_COLORS["harvest"],
                )
            )
            dtm_max = species.days_to_maturity_max
            if dtm_max and dtm_max > species.days_to_maturity_min:
                harvest_end = anchor + timedelta(days=dtm_max)
                events.append(
                    _make_event(
                        garden_id=garden.id,
                        planting_id=planting.id,
                        event_type="harvest",
                        title=f"Last harvest — {species.common_name}",
                        description=f"End of harvest window ({dtm_max} days from sow).",
                        scheduled_date=harvest_end,
                        source="auto",
                        priority="medium",
                        weather_dependent=False,
                        color=_EVENT_COLORS["harvest"],
                    )
                )

        # Periodic care events
        if anchor is not None:
            for offset, etype, title in _CARE_SCHEDULE:
                events.append(
                    _make_event(
                        garden_id=garden.id,
                        planting_id=planting.id,
                        event_type=etype,
                        title=f"{title} — {species.common_name}",
                        scheduled_date=anchor + timedelta(days=offset),
                        source="auto",
                        priority="low",
                        weather_dependent=False,
                        color=_EVENT_COLORS.get(etype),
                    )
                )

        # End-of-season removal (before first fall frost for frost-sensitive)
        if first_fall_frost is not None and is_frost_sensitive:
            remove_date = first_fall_frost - timedelta(days=3)
            events.append(
                _make_event(
                    garden_id=garden.id,
                    planting_id=planting.id,
                    event_type="remove",
                    title=f"Remove {species.common_name} before frost",
                    description=f"First fall frost expected around {first_fall_frost}.",
                    scheduled_date=remove_date,
                    source="auto",
                    priority="medium",
                    weather_dependent=True,
                    color=_EVENT_COLORS["remove"],
                )
            )

        # Persist
        for event in events:
            db.add(event)
        await db.flush()
        return events

    async def generate_weather_alerts(
        self,
        garden: Garden,
        db: AsyncSession,
    ) -> list[CalendarEvent]:
        """Create calendar events for upcoming frost/extreme weather alerts."""
        alerts = await self._weather_svc.get_recent_weather_alerts(garden.id, db)
        events: list[CalendarEvent] = []
        for alert in alerts:
            alert_date = _parse_date(alert["date"]) or date.today()
            event = _make_event(
                garden_id=garden.id,
                planting_id=None,
                event_type="frost_alert",
                title=alert["message"],
                description=f"Severity: {alert['severity']}",
                scheduled_date=alert_date,
                source="weather",
                priority="high" if alert["severity"] == "high" else "medium",
                weather_dependent=True,
                color=_EVENT_COLORS["frost_alert"],
            )
            db.add(event)
            events.append(event)
        await db.flush()
        return events


# ── Helpers ────────────────────────────────────────────────────────────────────

def _determine_anchor(
    planting: Planting,
    species: PlantSpecies,
    last_spring_frost: date | None,
    is_frost_sensitive: bool,
) -> date | None:
    """Return the transplant/direct-sow anchor date for schedule generation."""
    if planting.date_transplanted:
        return planting.date_transplanted
    if planting.date_seeded and not is_frost_sensitive:
        return planting.date_seeded
    if last_spring_frost is not None:
        # Frost-sensitive: transplant on last frost date; hardy: 2 weeks before
        if is_frost_sensitive:
            return last_spring_frost
        else:
            return last_spring_frost - timedelta(weeks=2)
    # No frost data — use today + 2 weeks as placeholder
    return date.today() + timedelta(weeks=2)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _make_event(
    *,
    garden_id: int,
    planting_id: int | None,
    event_type: str,
    title: str,
    scheduled_date: date,
    source: str,
    priority: str,
    weather_dependent: bool,
    color: str | None = None,
    description: str | None = None,
) -> CalendarEvent:
    return CalendarEvent(
        garden_id=garden_id,
        planting_id=planting_id,
        event_type=event_type,
        title=title,
        description=description,
        scheduled_date=scheduled_date,
        source=source,
        priority=priority,
        weather_dependent=weather_dependent,
        color=color,
        created_at=datetime.now(UTC),
    )

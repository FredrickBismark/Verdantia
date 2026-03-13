"""Tests for CalendarService — schedule generation, weather alerts, rescheduling."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, patch

from verdanta.models.garden import Garden
from verdanta.models.plant import PlantSpecies
from verdanta.models.planting import CalendarEvent, Planting
from verdanta.services.calendar_service import CalendarService

# ── Helpers ─────────────────────────────────────────────────────────────────────

def _make_garden(db_session) -> Garden:
    garden = Garden(
        name="Test Garden",
        latitude=51.5,
        longitude=-0.1,
        timezone="UTC",
    )
    db_session.add(garden)
    return garden


def _make_species(
    db_session,
    *,
    frost_tolerance: str = "tender",
    days_min: int | None = 60,
    days_max: int | None = 80,
) -> PlantSpecies:
    species = PlantSpecies(
        common_name="Test Tomato",
        frost_tolerance=frost_tolerance,
        days_to_maturity_min=days_min,
        days_to_maturity_max=days_max,
    )
    db_session.add(species)
    return species


def _make_planting(db_session, garden: Garden, species: PlantSpecies) -> Planting:
    planting = Planting(
        garden_id=garden.id,
        species_id=species.id,
        quantity=4,
        status="planned",
    )
    db_session.add(planting)
    return planting


def _no_frost_data() -> dict:
    return {
        "last_spring_frost": None,
        "first_fall_frost": None,
    }


def _frost_data(spring: date, fall: date) -> dict:
    return {
        "last_spring_frost": spring.isoformat(),
        "first_fall_frost": fall.isoformat(),
    }


# ── generate_schedule ────────────────────────────────────────────────────────────

async def test_generate_schedule_frost_sensitive_with_frost_dates(db_session):
    """Frost-sensitive species with known frost dates gets seed_indoors + transplant."""
    garden = _make_garden(db_session)
    species = _make_species(db_session, frost_tolerance="tender")
    await db_session.flush()
    planting = _make_planting(db_session, garden, species)
    await db_session.flush()

    spring_frost = date.today() + timedelta(weeks=8)
    fall_frost = date.today() + timedelta(weeks=30)

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "estimate_frost_dates",
        new=AsyncMock(return_value=_frost_data(spring_frost, fall_frost)),
    ):
        events = await svc.generate_schedule(planting, species, garden, db_session)

    event_types = {e.event_type for e in events}
    assert "seed_indoors" in event_types
    assert "transplant" in event_types
    assert "harvest" in event_types
    assert "fertilize" in event_types
    assert "pest_check" in event_types
    assert "remove" in event_types


async def test_generate_schedule_direct_sow_frost_hardy(db_session):
    """Hardy species gets direct_sow instead of seed_indoors/transplant."""
    garden = _make_garden(db_session)
    species = _make_species(db_session, frost_tolerance="very hardy")
    await db_session.flush()
    planting = _make_planting(db_session, garden, species)
    await db_session.flush()

    spring_frost = date.today() + timedelta(weeks=6)
    fall_frost = date.today() + timedelta(weeks=28)

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "estimate_frost_dates",
        new=AsyncMock(return_value=_frost_data(spring_frost, fall_frost)),
    ):
        events = await svc.generate_schedule(planting, species, garden, db_session)

    event_types = {e.event_type for e in events}
    assert "direct_sow" in event_types
    assert "seed_indoors" not in event_types
    assert "transplant" not in event_types
    # No fall-frost remove event for hardy plants
    assert "remove" not in event_types


async def test_generate_schedule_no_frost_data_uses_fallback_anchor(db_session):
    """Without frost data the schedule falls back to today + 2 weeks as anchor."""
    garden = _make_garden(db_session)
    species = _make_species(db_session, frost_tolerance="tender")
    await db_session.flush()
    planting = _make_planting(db_session, garden, species)
    await db_session.flush()

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "estimate_frost_dates",
        new=AsyncMock(return_value=_no_frost_data()),
    ):
        events = await svc.generate_schedule(planting, species, garden, db_session)

    # Should still produce transplant and care events using fallback anchor
    event_types = {e.event_type for e in events}
    assert "transplant" in event_types or "direct_sow" in event_types
    assert "fertilize" in event_types


async def test_generate_schedule_uses_recorded_transplant_date(db_session):
    """If planting already has a transplant date, it is used as anchor directly."""
    garden = _make_garden(db_session)
    species = _make_species(db_session, frost_tolerance="tender", days_min=50, days_max=70)
    await db_session.flush()
    transplant_date = date.today() + timedelta(days=5)
    planting = Planting(
        garden_id=garden.id,
        species_id=species.id,
        quantity=1,
        status="planted",
        date_transplanted=transplant_date,
    )
    db_session.add(planting)
    await db_session.flush()

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "estimate_frost_dates",
        new=AsyncMock(return_value=_no_frost_data()),
    ):
        events = await svc.generate_schedule(planting, species, garden, db_session)

    # The transplant event is still generated (to mark it on calendar)
    # but anchor-based harvest should be relative to transplant_date
    harvest_events = [e for e in events if e.event_type == "harvest"]
    assert harvest_events
    first_harvest = min(e.scheduled_date for e in harvest_events)
    assert first_harvest == transplant_date + timedelta(days=50)


async def test_generate_schedule_no_harvest_without_maturity_days(db_session):
    """Species without days_to_maturity produces no harvest events."""
    garden = _make_garden(db_session)
    species = _make_species(db_session, frost_tolerance="hardy", days_min=None, days_max=None)
    await db_session.flush()
    planting = _make_planting(db_session, garden, species)
    await db_session.flush()

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "estimate_frost_dates",
        new=AsyncMock(return_value=_no_frost_data()),
    ):
        events = await svc.generate_schedule(planting, species, garden, db_session)

    assert not any(e.event_type == "harvest" for e in events)


async def test_generate_schedule_events_persisted_to_db(db_session):
    """Events are flushed to the DB session so they have IDs after generation."""
    from sqlalchemy import select

    garden = _make_garden(db_session)
    species = _make_species(db_session)
    await db_session.flush()
    planting = _make_planting(db_session, garden, species)
    await db_session.flush()

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "estimate_frost_dates",
        new=AsyncMock(return_value=_no_frost_data()),
    ):
        events = await svc.generate_schedule(planting, species, garden, db_session)

    assert all(e.id is not None for e in events)
    result = await db_session.execute(
        select(CalendarEvent).where(CalendarEvent.garden_id == garden.id)
    )
    db_events = result.scalars().all()
    assert len(db_events) == len(events)


# ── generate_weather_alerts ───────────────────────────────────────────────────────

async def test_generate_weather_alerts_creates_frost_event(db_session):
    """A frost alert creates a frost_alert CalendarEvent."""
    garden = _make_garden(db_session)
    await db_session.flush()

    alert_date = date.today() + timedelta(days=2)
    fake_alerts = [
        {
            "type": "frost",
            "severity": "high",
            "date": alert_date.isoformat(),
            "message": "Frost risk on 2026-03-15 — min temp -2°C",
        }
    ]

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "get_recent_weather_alerts",
        new=AsyncMock(return_value=fake_alerts),
    ):
        events = await svc.generate_weather_alerts(garden, db_session)

    assert len(events) == 1
    assert events[0].event_type == "frost_alert"
    assert events[0].scheduled_date == alert_date
    assert events[0].source == "weather"
    assert events[0].priority == "high"


async def test_generate_weather_alerts_empty_when_no_alerts(db_session):
    """No alerts → no events created."""
    garden = _make_garden(db_session)
    await db_session.flush()

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "get_recent_weather_alerts",
        new=AsyncMock(return_value=[]),
    ):
        events = await svc.generate_weather_alerts(garden, db_session)

    assert events == []


# ── reschedule_weather_dependent ─────────────────────────────────────────────────

async def test_reschedule_weather_dependent_shifts_conflicting_event(db_session):
    """A weather_dependent event on an alert day gets pushed to the next clear day."""
    garden = _make_garden(db_session)
    await db_session.flush()

    alert_date = date.today() + timedelta(days=1)
    event = CalendarEvent(
        garden_id=garden.id,
        event_type="transplant",
        title="Transplant Tomato",
        scheduled_date=alert_date,
        source="auto",
        weather_dependent=True,
        completed=False,
        created_at=datetime.now(UTC),
    )
    db_session.add(event)
    await db_session.flush()

    svc = CalendarService()
    fake_alerts = [
        {
            "type": "frost",
            "severity": "high",
            "date": alert_date.isoformat(),
            "message": "Frost",
        }
    ]
    with patch.object(
        svc._weather_svc,
        "get_recent_weather_alerts",
        new=AsyncMock(return_value=fake_alerts),
    ):
        rescheduled = await svc.reschedule_weather_dependent(garden, db_session)

    assert len(rescheduled) == 1
    assert rescheduled[0].scheduled_date == alert_date + timedelta(days=1)


async def test_reschedule_skips_completed_events(db_session):
    """Completed events are never rescheduled."""
    garden = _make_garden(db_session)
    await db_session.flush()

    alert_date = date.today() + timedelta(days=1)
    event = CalendarEvent(
        garden_id=garden.id,
        event_type="transplant",
        title="Done",
        scheduled_date=alert_date,
        source="auto",
        weather_dependent=True,
        completed=True,
        completed_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    db_session.add(event)
    await db_session.flush()

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "get_recent_weather_alerts",
        new=AsyncMock(
            return_value=[
                {
                    "type": "frost",
                    "severity": "high",
                    "date": alert_date.isoformat(),
                    "message": "Frost",
                }
            ]
        ),
    ):
        rescheduled = await svc.reschedule_weather_dependent(garden, db_session)

    assert rescheduled == []


async def test_reschedule_skips_non_weather_dependent_events(db_session):
    """Events with weather_dependent=False are left alone."""
    garden = _make_garden(db_session)
    await db_session.flush()

    alert_date = date.today() + timedelta(days=1)
    event = CalendarEvent(
        garden_id=garden.id,
        event_type="fertilize",
        title="Fertilize",
        scheduled_date=alert_date,
        source="auto",
        weather_dependent=False,
        completed=False,
        created_at=datetime.now(UTC),
    )
    db_session.add(event)
    await db_session.flush()

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "get_recent_weather_alerts",
        new=AsyncMock(
            return_value=[
                {
                    "type": "frost",
                    "severity": "high",
                    "date": alert_date.isoformat(),
                    "message": "Frost",
                }
            ]
        ),
    ):
        rescheduled = await svc.reschedule_weather_dependent(garden, db_session)

    assert rescheduled == []


async def test_reschedule_skips_consecutive_alert_days(db_session):
    """Event on day 1 of a 2-day alert window is shifted past both alert days."""
    garden = _make_garden(db_session)
    await db_session.flush()

    day1 = date.today() + timedelta(days=1)
    day2 = date.today() + timedelta(days=2)

    event = CalendarEvent(
        garden_id=garden.id,
        event_type="transplant",
        title="Transplant",
        scheduled_date=day1,
        source="auto",
        weather_dependent=True,
        completed=False,
        created_at=datetime.now(UTC),
    )
    db_session.add(event)
    await db_session.flush()

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "get_recent_weather_alerts",
        new=AsyncMock(
            return_value=[
                {"type": "frost", "severity": "high", "date": day1.isoformat(), "message": ""},
                {"type": "frost", "severity": "high", "date": day2.isoformat(), "message": ""},
            ]
        ),
    ):
        rescheduled = await svc.reschedule_weather_dependent(garden, db_session)

    assert len(rescheduled) == 1
    assert rescheduled[0].scheduled_date == day2 + timedelta(days=1)


async def test_reschedule_no_alerts_returns_empty(db_session):
    """No weather alerts → nothing rescheduled."""
    garden = _make_garden(db_session)
    await db_session.flush()

    svc = CalendarService()
    with patch.object(
        svc._weather_svc,
        "get_recent_weather_alerts",
        new=AsyncMock(return_value=[]),
    ):
        rescheduled = await svc.reschedule_weather_dependent(garden, db_session)

    assert rescheduled == []

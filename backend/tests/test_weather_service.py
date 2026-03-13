"""Tests for WeatherService — GDD, frost dates, alerts, sync deduplication."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from verdanta.models.garden import Garden
from verdanta.models.weather import WeatherRecord
from verdanta.services.weather_service import WeatherService

# ── Helpers ─────────────────────────────────────────────────────────────────────

def _make_garden(db_session) -> Garden:
    garden = Garden(
        name="Weather Test Garden",
        latitude=51.5,
        longitude=-0.1,
        timezone="UTC",
    )
    db_session.add(garden)
    return garden


def _forecast_record(
    db_session,
    garden_id: int,
    *,
    days_offset: int,
    tmin: float,
    tmax: float,
    precipitation_mm: float = 0.0,
) -> WeatherRecord:
    ts = datetime.now(UTC) + timedelta(days=days_offset)
    rec = WeatherRecord(
        garden_id=garden_id,
        record_type="forecast",
        source="open-meteo",
        timestamp=ts,
        temp_c=(tmax + tmin) / 2,
        temp_min_c=tmin,
        temp_max_c=tmax,
        precipitation_mm=precipitation_mm,
        frost_risk=tmin <= 2.0,
        fetched_at=datetime.now(UTC),
    )
    db_session.add(rec)
    return rec


def _historical_record(
    db_session,
    garden_id: int,
    *,
    days_offset: int,
    tmin: float,
    tmax: float,
    frost: bool = False,
) -> WeatherRecord:
    ts = datetime.now(UTC) + timedelta(days=days_offset)
    rec = WeatherRecord(
        garden_id=garden_id,
        record_type="historical",
        source="open-meteo-archive",
        timestamp=ts,
        temp_c=(tmax + tmin) / 2,
        temp_min_c=tmin,
        temp_max_c=tmax,
        frost_risk=frost,
        fetched_at=datetime.now(UTC),
    )
    db_session.add(rec)
    return rec


# ── calculate_gdd ────────────────────────────────────────────────────────────────

def test_calculate_gdd_basic():
    svc = WeatherService()
    # avg = (25+15)/2 = 20; GDD = 20 - 10 = 10
    assert svc.calculate_gdd(15.0, 25.0, base_temp_c=10.0, cap_temp_c=None) == pytest.approx(10.0)


def test_calculate_gdd_below_base_returns_zero():
    svc = WeatherService()
    # avg = (5+1)/2 = 3; below base 10 → 0
    assert svc.calculate_gdd(1.0, 5.0, base_temp_c=10.0, cap_temp_c=None) == pytest.approx(0.0)


def test_calculate_gdd_cap_applied():
    svc = WeatherService()
    # cap at 30: tmax stays 25, tmin stays 5
    # tmin = max(5, 10) = 10 (base clamp), tmax = min(40, 30) = 30 (cap clamp)
    # avg = (30+10)/2 = 20; GDD = 20 - 10 = 10
    result = svc.calculate_gdd(5.0, 40.0, base_temp_c=10.0, cap_temp_c=30.0)
    assert result == pytest.approx(10.0)


def test_calculate_gdd_exact_base():
    svc = WeatherService()
    # avg = (10+10)/2 = 10; GDD = 0
    assert svc.calculate_gdd(10.0, 10.0, base_temp_c=10.0) == pytest.approx(0.0)


# ── accumulated_gdd ──────────────────────────────────────────────────────────────

async def test_accumulated_gdd_sums_records(db_session):
    garden = _make_garden(db_session)
    await db_session.flush()

    _historical_record(db_session, garden.id, days_offset=-3, tmin=5.0, tmax=25.0)
    _historical_record(db_session, garden.id, days_offset=-2, tmin=6.0, tmax=22.0)
    _historical_record(db_session, garden.id, days_offset=-1, tmin=8.0, tmax=20.0)
    await db_session.flush()

    svc = WeatherService()
    start = date.today() - timedelta(days=10)
    result = await svc.accumulated_gdd(garden.id, db_session, start_date=start, base_temp_c=10.0)

    assert result["garden_id"] == garden.id
    assert result["base_temp_c"] == 10.0
    assert len(result["daily"]) == 3
    assert result["total_gdd"] > 0
    # Accumulated values should be non-decreasing
    accumulated = [d["accumulated"] for d in result["daily"]]
    assert accumulated == sorted(accumulated)


async def test_accumulated_gdd_no_records_returns_empty(db_session):
    garden = _make_garden(db_session)
    await db_session.flush()

    svc = WeatherService()
    result = await svc.accumulated_gdd(garden.id, db_session, base_temp_c=10.0)

    assert result["total_gdd"] == 0.0
    assert result["daily"] == []


# ── estimate_frost_dates ─────────────────────────────────────────────────────────

async def test_estimate_frost_dates_no_data(db_session):
    garden = _make_garden(db_session)
    await db_session.flush()

    svc = WeatherService()
    result = await svc.estimate_frost_dates(garden.id, db_session)

    assert result["last_spring_frost"] is None
    assert result["first_fall_frost"] is None
    assert "note" in result


async def test_estimate_frost_dates_with_frost_records(db_session):
    """Frost records in spring and fall populate the estimate correctly."""
    garden = _make_garden(db_session)
    await db_session.flush()

    today = datetime.now(UTC)
    this_year = today.year

    # Spring frost record (April = early in year)
    spring_ts = datetime(this_year, 4, 10, tzinfo=UTC)
    db_session.add(WeatherRecord(
        garden_id=garden.id,
        record_type="historical",
        source="open-meteo-archive",
        timestamp=spring_ts,
        frost_risk=True,
        fetched_at=datetime.now(UTC),
    ))
    # Fall frost record (October = late in year)
    fall_ts = datetime(this_year, 10, 15, tzinfo=UTC)
    db_session.add(WeatherRecord(
        garden_id=garden.id,
        record_type="historical",
        source="open-meteo-archive",
        timestamp=fall_ts,
        frost_risk=True,
        fetched_at=datetime.now(UTC),
    ))
    await db_session.flush()

    svc = WeatherService()
    result = await svc.estimate_frost_dates(garden.id, db_session)

    assert result["data_points"] == 2
    # Spring frost should be in the first half of the year
    if result["last_spring_frost"]:
        spring = date.fromisoformat(result["last_spring_frost"])
        assert spring.month < 7
    # Fall frost should be in the second half
    if result["first_fall_frost"]:
        fall = date.fromisoformat(result["first_fall_frost"])
        assert fall.month >= 7


# ── get_recent_weather_alerts ─────────────────────────────────────────────────────

async def test_get_recent_weather_alerts_frost_detected(db_session):
    garden = _make_garden(db_session)
    await db_session.flush()

    # Forecast record within 3 days with frost risk
    _forecast_record(db_session, garden.id, days_offset=1, tmin=-2.0, tmax=5.0)
    await db_session.flush()

    svc = WeatherService()
    alerts = await svc.get_recent_weather_alerts(garden.id, db_session)

    frost_alerts = [a for a in alerts if a["type"] == "frost"]
    assert len(frost_alerts) == 1
    assert frost_alerts[0]["severity"] == "high"


async def test_get_recent_weather_alerts_heavy_rain_detected(db_session):
    garden = _make_garden(db_session)
    await db_session.flush()

    _forecast_record(
        db_session, garden.id, days_offset=2, tmin=10.0, tmax=18.0, precipitation_mm=30.0
    )
    await db_session.flush()

    svc = WeatherService()
    alerts = await svc.get_recent_weather_alerts(garden.id, db_session)

    rain_alerts = [a for a in alerts if a["type"] == "heavy_rain"]
    assert len(rain_alerts) == 1
    assert rain_alerts[0]["severity"] == "medium"


async def test_get_recent_weather_alerts_no_alerts(db_session):
    garden = _make_garden(db_session)
    await db_session.flush()

    # Mild weather — no frost, no heavy rain
    _forecast_record(db_session, garden.id, days_offset=1, tmin=10.0, tmax=20.0)
    await db_session.flush()

    svc = WeatherService()
    alerts = await svc.get_recent_weather_alerts(garden.id, db_session)

    assert alerts == []


async def test_get_recent_weather_alerts_excludes_far_future(db_session):
    """Records beyond days_ahead=3 are not included."""
    garden = _make_garden(db_session)
    await db_session.flush()

    # 10 days out — outside the 3-day window
    _forecast_record(db_session, garden.id, days_offset=10, tmin=-5.0, tmax=0.0)
    await db_session.flush()

    svc = WeatherService()
    alerts = await svc.get_recent_weather_alerts(garden.id, db_session, days_ahead=3)

    assert alerts == []


# ── sync_garden deduplication ────────────────────────────────────────────────────

async def test_sync_garden_replaces_existing_forecast_records(db_session):
    """sync_garden deletes old current/forecast rows before inserting fresh ones."""
    from sqlalchemy import select

    garden = _make_garden(db_session)
    await db_session.flush()

    # Pre-existing stale forecast record
    stale = WeatherRecord(
        garden_id=garden.id,
        record_type="forecast",
        source="open-meteo",
        timestamp=datetime.now(UTC),
        fetched_at=datetime.now(UTC),
    )
    db_session.add(stale)
    await db_session.flush()
    _ = stale.id  # capture before sync overwrites identity map

    # Minimal fake API response
    fake_response_data = {
        "current": {
            "temperature_2m": 15.0,
            "relative_humidity_2m": 70,
            "precipitation": 0.0,
            "wind_speed_10m": 5.0,
            "cloud_cover": 20,
            "uv_index": 3.0,
        },
        "daily": {
            "time": [(date.today() + timedelta(days=i)).isoformat() for i in range(3)],
            "temperature_2m_max": [20.0, 22.0, 18.0],
            "temperature_2m_min": [10.0, 12.0, 8.0],
            "precipitation_sum": [0.0, 0.0, 5.0],
            "wind_speed_10m_max": [10.0, 12.0, 8.0],
            "uv_index_max": [4.0, 5.0, 3.0],
        },
    }

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=fake_response_data)

    svc = WeatherService()
    with patch(
        "verdanta.services.weather_service._http_client.get",
        new=AsyncMock(return_value=mock_resp),
    ):
        result = await svc.sync_garden(garden, db_session)

    await db_session.flush()

    # Use COUNT (aggregate bypasses the ORM identity map) to check that only
    # the newly synced rows are present — stale row should be gone (1→0) and
    # new rows added (0→4).
    from sqlalchemy import func

    count_result = await db_session.execute(
        select(func.count()).select_from(WeatherRecord).where(
            WeatherRecord.garden_id == garden.id,
            WeatherRecord.record_type.in_(["current", "forecast"]),
        )
    )
    total = count_result.scalar_one()
    # 1 current + 3 forecast = 4 (the original stale forecast replaced)
    assert total == 4
    assert result["synced"] == 4


async def test_sync_garden_preserves_historical_records(db_session):
    """sync_garden must NOT delete historical records — only current and forecast."""
    from sqlalchemy import select

    garden = _make_garden(db_session)
    await db_session.flush()

    historical = WeatherRecord(
        garden_id=garden.id,
        record_type="historical",
        source="open-meteo-archive",
        timestamp=datetime(2025, 6, 15, tzinfo=UTC),
        fetched_at=datetime.now(UTC),
    )
    db_session.add(historical)
    await db_session.flush()
    historical_id = historical.id

    fake_response_data = {
        "current": {
            "temperature_2m": 15.0,
            "relative_humidity_2m": 70,
            "precipitation": 0.0,
            "wind_speed_10m": 5.0,
            "cloud_cover": 20,
            "uv_index": 3.0,
        },
        "daily": {"time": [], "temperature_2m_max": [], "temperature_2m_min": [],
                  "precipitation_sum": [], "wind_speed_10m_max": [], "uv_index_max": []},
    }
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=fake_response_data)

    svc = WeatherService()
    with patch(
        "verdanta.services.weather_service._http_client.get",
        new=AsyncMock(return_value=mock_resp),
    ):
        await svc.sync_garden(garden, db_session)

    await db_session.flush()

    kept = await db_session.execute(
        select(WeatherRecord).where(WeatherRecord.id == historical_id)
    )
    assert kept.scalar_one_or_none() is not None

"""Weather service — Open-Meteo integration (free, no API key required).

Fetches current conditions, 7-day forecasts, and historical data.
Calculates Growing Degree Days (GDD) and estimates frost dates from records.
"""

import logging
from datetime import UTC, date, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.models.garden import Garden
from verdanta.models.weather import WeatherRecord

logger = logging.getLogger(__name__)

_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

_CURRENT_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "cloud_cover",
    "uv_index",
]
_DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
    "uv_index_max",
]
_ARCHIVE_DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
]


class WeatherService:
    """Handles weather data fetching, storage, and derived calculations."""

    # ── Fetching ──────────────────────────────────────────────────────────────

    async def fetch_current_and_forecast(
        self,
        garden: Garden,
        forecast_days: int = 7,
    ) -> list[dict]:
        """Fetch current conditions + daily forecast from Open-Meteo."""
        params: dict = {
            "latitude": garden.latitude,
            "longitude": garden.longitude,
            "current": ",".join(_CURRENT_VARS),
            "daily": ",".join(_DAILY_VARS),
            "timezone": garden.timezone or "UTC",
            "forecast_days": forecast_days,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(_FORECAST_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        records: list[dict] = []

        # Current conditions
        if "current" in data:
            cur = data["current"]
            temp = cur.get("temperature_2m")
            records.append(
                {
                    "record_type": "current",
                    "source": "open-meteo",
                    "timestamp": datetime.now(UTC),
                    "temp_c": temp,
                    "humidity_pct": cur.get("relative_humidity_2m"),
                    "precipitation_mm": cur.get("precipitation"),
                    "wind_speed_kmh": cur.get("wind_speed_10m"),
                    "cloud_cover_pct": cur.get("cloud_cover"),
                    "uv_index": cur.get("uv_index"),
                    "frost_risk": temp is not None and temp <= 2.0,
                    "raw_data": cur,
                }
            )

        # Daily forecasts
        if "daily" in data:
            daily = data["daily"]
            times: list[str] = daily.get("time", [])
            for i, day_str in enumerate(times):
                tmax = _get(daily, "temperature_2m_max", i)
                tmin = _get(daily, "temperature_2m_min", i)
                records.append(
                    {
                        "record_type": "forecast",
                        "source": "open-meteo",
                        "timestamp": datetime.fromisoformat(day_str).replace(tzinfo=UTC),
                        "temp_c": (
                            (tmax + tmin) / 2 if tmax is not None and tmin is not None else None
                        ),
                        "temp_min_c": tmin,
                        "temp_max_c": tmax,
                        "precipitation_mm": _get(daily, "precipitation_sum", i),
                        "wind_speed_kmh": _get(daily, "wind_speed_10m_max", i),
                        "uv_index": _get(daily, "uv_index_max", i),
                        "frost_risk": tmin is not None and tmin <= 2.0,
                        "raw_data": {
                            k: v[i] if isinstance(v, list) else v
                            for k, v in daily.items()
                        },
                    }
                )

        return records

    async def fetch_historical(
        self,
        garden: Garden,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Fetch historical daily data from Open-Meteo archive API."""
        params: dict = {
            "latitude": garden.latitude,
            "longitude": garden.longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": ",".join(_ARCHIVE_DAILY_VARS),
            "timezone": garden.timezone or "UTC",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(_ARCHIVE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        records: list[dict] = []
        if "daily" in data:
            daily = data["daily"]
            for i, day_str in enumerate(daily.get("time", [])):
                tmax = _get(daily, "temperature_2m_max", i)
                tmin = _get(daily, "temperature_2m_min", i)
                records.append(
                    {
                        "record_type": "historical",
                        "source": "open-meteo-archive",
                        "timestamp": datetime.fromisoformat(day_str).replace(tzinfo=UTC),
                        "temp_min_c": tmin,
                        "temp_max_c": tmax,
                        "temp_c": (
                            (tmax + tmin) / 2 if tmax is not None and tmin is not None else None
                        ),
                        "precipitation_mm": _get(daily, "precipitation_sum", i),
                        "frost_risk": tmin is not None and tmin <= 2.0,
                        "raw_data": {
                            k: v[i] if isinstance(v, list) else v
                            for k, v in daily.items()
                        },
                    }
                )
        return records

    # ── Storage ───────────────────────────────────────────────────────────────

    async def store_records(
        self,
        garden_id: int,
        records: list[dict],
        db: AsyncSession,
    ) -> list[WeatherRecord]:
        """Persist a list of record dicts to the database."""
        stored: list[WeatherRecord] = []
        for r in records:
            record = WeatherRecord(garden_id=garden_id, **r)
            db.add(record)
            stored.append(record)
        await db.flush()
        return stored

    async def sync_garden(
        self,
        garden: Garden,
        db: AsyncSession,
        forecast_days: int = 7,
    ) -> dict:
        """Full sync: fetch current + forecast, store results."""
        records = await self.fetch_current_and_forecast(garden, forecast_days)
        stored = await self.store_records(garden.id, records, db)
        return {
            "synced": len(stored),
            "garden_id": garden.id,
            "synced_at": datetime.now(UTC).isoformat(),
        }

    # ── Derived calculations ──────────────────────────────────────────────────

    def calculate_gdd(
        self,
        tmin_c: float,
        tmax_c: float,
        base_temp_c: float = 10.0,
        cap_temp_c: float | None = 30.0,
    ) -> float:
        """Calculate Growing Degree Days for a single day (simple average method).

        GDD = max(((tmax + tmin) / 2) - base, 0)
        Temperatures are capped at cap_temp_c when provided.
        """
        if cap_temp_c is not None:
            tmin_c = min(tmin_c, cap_temp_c)
            tmax_c = min(tmax_c, cap_temp_c)
        tmin_c = max(tmin_c, base_temp_c)
        avg = (tmax_c + tmin_c) / 2
        return max(avg - base_temp_c, 0.0)

    async def accumulated_gdd(
        self,
        garden_id: int,
        db: AsyncSession,
        start_date: date | None = None,
        base_temp_c: float = 10.0,
    ) -> dict:
        """Sum accumulated GDD from stored records since start_date (default Jan 1)."""
        if start_date is None:
            today = date.today()
            start_date = date(today.year, 1, 1)

        query = (
            select(WeatherRecord)
            .where(WeatherRecord.garden_id == garden_id)
            .where(WeatherRecord.record_type.in_(["historical", "forecast", "current"]))
            .where(
                WeatherRecord.timestamp
                >= datetime(start_date.year, start_date.month, start_date.day, tzinfo=UTC)
            )
            .where(WeatherRecord.temp_min_c.is_not(None))
            .where(WeatherRecord.temp_max_c.is_not(None))
            .order_by(WeatherRecord.timestamp)
        )
        result = await db.execute(query)
        records = result.scalars().all()

        total_gdd = 0.0
        daily: list[dict] = []
        for rec in records:
            gdd = self.calculate_gdd(
                rec.temp_min_c,  # type: ignore[arg-type]
                rec.temp_max_c,  # type: ignore[arg-type]
                base_temp_c,
            )
            total_gdd += gdd
            daily.append(
                {
                    "date": rec.timestamp.date().isoformat(),
                    "gdd": round(gdd, 2),
                    "accumulated": round(total_gdd, 2),
                }
            )

        return {
            "garden_id": garden_id,
            "start_date": start_date.isoformat(),
            "base_temp_c": base_temp_c,
            "total_gdd": round(total_gdd, 2),
            "daily": daily,
        }

    async def estimate_frost_dates(
        self,
        garden_id: int,
        db: AsyncSession,
    ) -> dict:
        """Estimate last spring frost and first fall frost from stored records."""
        query = (
            select(WeatherRecord)
            .where(WeatherRecord.garden_id == garden_id)
            .where(WeatherRecord.frost_risk.is_(True))
            .order_by(WeatherRecord.timestamp)
        )
        result = await db.execute(query)
        frost_records = result.scalars().all()

        if not frost_records:
            return {
                "garden_id": garden_id,
                "last_spring_frost": None,
                "first_fall_frost": None,
                "data_points": 0,
                "note": (
                    "No frost records found. "
                    "Sync weather data to enable frost date estimation."
                ),
            }

        today = date.today()
        current_year_frosts = [r for r in frost_records if r.timestamp.year == today.year]
        spring_frosts = [r for r in current_year_frosts if r.timestamp.month <= 6]
        fall_frosts = [r for r in current_year_frosts if r.timestamp.month >= 7]

        last_spring = max((r.timestamp.date() for r in spring_frosts), default=None)
        first_fall = min((r.timestamp.date() for r in fall_frosts), default=None)

        # Fall back to most recent year's data when current year lacks coverage
        if last_spring is None:
            spring_all = [r for r in frost_records if r.timestamp.month <= 6]
            if spring_all:
                most_recent_year = max(r.timestamp.year for r in spring_all)
                year_spring = [r for r in spring_all if r.timestamp.year == most_recent_year]
                last_spring = max(r.timestamp.date() for r in year_spring)

        if first_fall is None:
            fall_all = [r for r in frost_records if r.timestamp.month >= 7]
            if fall_all:
                most_recent_year = max(r.timestamp.year for r in fall_all)
                year_fall = [r for r in fall_all if r.timestamp.year == most_recent_year]
                first_fall = min(r.timestamp.date() for r in year_fall)

        return {
            "garden_id": garden_id,
            "last_spring_frost": last_spring.isoformat() if last_spring else None,
            "first_fall_frost": first_fall.isoformat() if first_fall else None,
            "data_points": len(frost_records),
            "growing_season_days": (
                (first_fall - last_spring).days
                if last_spring and first_fall and first_fall > last_spring
                else None
            ),
        }

    async def get_recent_weather_alerts(
        self,
        garden_id: int,
        db: AsyncSession,
        days_ahead: int = 3,
    ) -> list[dict]:
        """Return frost/extreme weather alerts from upcoming forecast records."""
        cutoff = datetime.now(UTC) + timedelta(days=days_ahead)
        query = (
            select(WeatherRecord)
            .where(WeatherRecord.garden_id == garden_id)
            .where(WeatherRecord.record_type == "forecast")
            .where(WeatherRecord.timestamp <= cutoff)
            .order_by(WeatherRecord.timestamp)
        )
        result = await db.execute(query)
        records = result.scalars().all()

        alerts: list[dict] = []
        for rec in records:
            if rec.frost_risk:
                alerts.append(
                    {
                        "type": "frost",
                        "severity": "high",
                        "date": rec.timestamp.date().isoformat(),
                        "message": (
                            f"Frost risk on {rec.timestamp.date()} "
                            f"— min temp {rec.temp_min_c}°C"
                        ),
                    }
                )
            if rec.precipitation_mm is not None and rec.precipitation_mm >= 25:
                alerts.append(
                    {
                        "type": "heavy_rain",
                        "severity": "medium",
                        "date": rec.timestamp.date().isoformat(),
                        "message": (
                            f"Heavy rain forecast on {rec.timestamp.date()} "
                            f"— {rec.precipitation_mm}mm"
                        ),
                    }
                )
        return alerts


def _get(daily: dict, key: str, index: int) -> float | None:
    """Safely get a value from an Open-Meteo daily dict by index."""
    values = daily.get(key)
    if values is None or not isinstance(values, list) or index >= len(values):
        return None
    return values[index]

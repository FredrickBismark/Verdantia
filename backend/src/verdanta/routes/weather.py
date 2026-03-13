from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.garden import Garden
from verdanta.models.weather import WeatherRecord
from verdanta.schemas.weather import WeatherRecordResponse
from verdanta.services.weather_service import WeatherService

router = APIRouter()
_svc = WeatherService()


async def _get_garden(garden_id: int, db: AsyncSession) -> Garden:
    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    return garden


@router.get("/gardens/{garden_id}/weather/current", response_model=dict)
async def current_weather(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the most recent current-type weather record, syncing if none exists."""
    result = await db.execute(
        select(WeatherRecord)
        .where(WeatherRecord.garden_id == garden_id)
        .where(WeatherRecord.record_type == "current")
        .order_by(WeatherRecord.fetched_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if record is None:
        # Auto-sync if no data yet
        garden = await _get_garden(garden_id, db)
        try:
            await _svc.sync_garden(garden, db)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Weather sync failed: {exc}") from exc
        result = await db.execute(
            select(WeatherRecord)
            .where(WeatherRecord.garden_id == garden_id)
            .where(WeatherRecord.record_type == "current")
            .order_by(WeatherRecord.fetched_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="No weather data available")
    return {"data": WeatherRecordResponse.model_validate(record)}


@router.get("/gardens/{garden_id}/weather/forecast", response_model=dict)
async def forecast(
    garden_id: int,
    days: int = Query(7, ge=1, le=16),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return stored forecast records for the next N days."""
    result = await db.execute(
        select(WeatherRecord)
        .where(WeatherRecord.garden_id == garden_id)
        .where(WeatherRecord.record_type == "forecast")
        .order_by(WeatherRecord.timestamp)
        .limit(days)
    )
    records = result.scalars().all()
    if not records:
        garden = await _get_garden(garden_id, db)
        try:
            await _svc.sync_garden(garden, db, forecast_days=days)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Weather sync failed: {exc}") from exc
        result = await db.execute(
            select(WeatherRecord)
            .where(WeatherRecord.garden_id == garden_id)
            .where(WeatherRecord.record_type == "forecast")
            .order_by(WeatherRecord.timestamp)
            .limit(days)
        )
        records = result.scalars().all()
    return {
        "data": [WeatherRecordResponse.model_validate(r) for r in records],
        "count": len(records),
    }


@router.get("/gardens/{garden_id}/weather/historical", response_model=dict)
async def historical_weather(
    garden_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Fetch and store historical weather data for a date range."""
    garden = await _get_garden(garden_id, db)
    try:
        records_data = await _svc.fetch_historical(garden, start_date, end_date)
        stored = await _svc.store_records(garden_id, records_data, db)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Historical fetch failed: {exc}") from exc
    return {
        "data": [WeatherRecordResponse.model_validate(r) for r in stored],
        "count": len(stored),
    }


@router.post("/gardens/{garden_id}/weather/sync", response_model=dict)
async def sync_weather(
    garden_id: int,
    forecast_days: int = Query(7, ge=1, le=16),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger a full current + forecast sync for the garden."""
    garden = await _get_garden(garden_id, db)
    try:
        result = await _svc.sync_garden(garden, db, forecast_days=forecast_days)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Weather sync failed: {exc}") from exc
    return {"data": result}


@router.get("/gardens/{garden_id}/weather/frost-dates", response_model=dict)
async def frost_dates(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Estimate last spring frost and first fall frost from stored records."""
    await _get_garden(garden_id, db)
    result = await _svc.estimate_frost_dates(garden_id, db)
    return {"data": result}


@router.get("/gardens/{garden_id}/weather/gdd", response_model=dict)
async def growing_degree_days(
    garden_id: int,
    base_temp_c: float = Query(10.0),
    start_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return accumulated Growing Degree Days from stored records."""
    await _get_garden(garden_id, db)
    result = await _svc.accumulated_gdd(garden_id, db, start_date, base_temp_c)
    return {"data": result}

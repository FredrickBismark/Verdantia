from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db

router = APIRouter()


@router.get("/gardens/{garden_id}/weather/current", response_model=dict)
async def current_weather(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement weather service (Phase 3)
    return {"data": None, "message": "Weather service coming in Phase 3"}


@router.get("/gardens/{garden_id}/weather/forecast", response_model=dict)
async def forecast(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement weather service (Phase 3)
    return {"data": []}


@router.get("/gardens/{garden_id}/weather/historical", response_model=dict)
async def historical_weather(
    garden_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement weather service (Phase 3)
    return {"data": []}


@router.post("/gardens/{garden_id}/weather/sync", response_model=dict)
async def sync_weather(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement weather sync (Phase 3)
    return {"data": {"status": "not_implemented"}}


@router.get("/gardens/{garden_id}/weather/frost-dates", response_model=dict)
async def frost_dates(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement frost date estimation (Phase 3)
    return {"data": None}


@router.get("/gardens/{garden_id}/weather/gdd", response_model=dict)
async def growing_degree_days(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement GDD calculation (Phase 3)
    return {"data": None}

from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.planting import CalendarEvent
from verdanta.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
)

router = APIRouter()


@router.get("/gardens/{garden_id}/events", response_model=dict)
async def list_events(
    garden_id: int,
    plant_id: int | None = None,
    event_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    completed: bool | None = None,
    priority: str | None = None,
    source: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict:
    base_query = select(CalendarEvent).where(CalendarEvent.garden_id == garden_id)
    if plant_id:
        base_query = base_query.where(CalendarEvent.planting_id == plant_id)
    if event_type:
        base_query = base_query.where(CalendarEvent.event_type == event_type)
    if start_date:
        base_query = base_query.where(CalendarEvent.scheduled_date >= start_date)
    if end_date:
        base_query = base_query.where(CalendarEvent.scheduled_date <= end_date)
    if completed is not None:
        base_query = base_query.where(CalendarEvent.completed == completed)
    if priority:
        base_query = base_query.where(CalendarEvent.priority == priority)
    if source:
        base_query = base_query.where(CalendarEvent.source == source)
    result = await db.execute(base_query.offset(skip).limit(limit))
    events = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()
    return {"data": [CalendarEventResponse.model_validate(e) for e in events], "count": total}


@router.post("/gardens/{garden_id}/events", response_model=dict, status_code=201)
async def create_event(
    garden_id: int,
    event_in: CalendarEventCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    event = CalendarEvent(garden_id=garden_id, **event_in.model_dump())
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return {"data": CalendarEventResponse.model_validate(event)}


@router.get("/events/{event_id}", response_model=dict)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    event = await db.get(CalendarEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"data": CalendarEventResponse.model_validate(event)}


@router.put("/events/{event_id}", response_model=dict)
async def update_event(
    event_id: int,
    event_in: CalendarEventUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    event = await db.get(CalendarEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    for field, value in event_in.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    await db.flush()
    await db.refresh(event)
    return {"data": CalendarEventResponse.model_validate(event)}


@router.delete("/events/{event_id}", status_code=204)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    event = await db.get(CalendarEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(event)


@router.post("/events/{event_id}/complete", response_model=dict)
async def complete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    event = await db.get(CalendarEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.completed = True
    event.completed_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(event)
    return {"data": CalendarEventResponse.model_validate(event)}


@router.post("/gardens/{garden_id}/events/generate", response_model=dict)
async def generate_schedule(
    garden_id: int,
    planting_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Auto-generate a care schedule for a planting based on species data and frost dates."""
    from verdanta.models.garden import Garden
    from verdanta.models.planting import Planting
    from verdanta.services.calendar_service import CalendarService

    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    planting = await db.get(Planting, planting_id)
    if not planting or planting.garden_id != garden_id:
        raise HTTPException(status_code=404, detail="Planting not found in this garden")
    from verdanta.models.plant import PlantSpecies
    species = await db.get(PlantSpecies, planting.species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Plant species not found")

    svc = CalendarService()
    events = await svc.generate_schedule(planting, species, garden, db)
    return {
        "data": [CalendarEventResponse.model_validate(e) for e in events],
        "count": len(events),
    }


@router.get("/gardens/{garden_id}/events/weather-alerts", response_model=dict)
async def weather_alerts(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create calendar alert events for upcoming frost and extreme weather."""
    from verdanta.models.garden import Garden
    from verdanta.services.calendar_service import CalendarService

    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    svc = CalendarService()
    events = await svc.generate_weather_alerts(garden, db)
    return {
        "data": [CalendarEventResponse.model_validate(e) for e in events],
        "count": len(events),
    }

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.planting import CalendarEvent
from verdanta.schemas.calendar import CalendarEventCreate, CalendarEventResponse, CalendarEventUpdate

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
    query = select(CalendarEvent).where(CalendarEvent.garden_id == garden_id)
    if plant_id:
        query = query.where(CalendarEvent.planting_id == plant_id)
    if event_type:
        query = query.where(CalendarEvent.event_type == event_type)
    if start_date:
        query = query.where(CalendarEvent.scheduled_date >= start_date)
    if end_date:
        query = query.where(CalendarEvent.scheduled_date <= end_date)
    if completed is not None:
        query = query.where(CalendarEvent.completed == completed)
    if priority:
        query = query.where(CalendarEvent.priority == priority)
    if source:
        query = query.where(CalendarEvent.source == source)
    result = await db.execute(query.offset(skip).limit(limit))
    events = result.scalars().all()
    return {"data": [CalendarEventResponse.model_validate(e) for e in events], "count": len(events)}


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
    event.completed_at = datetime.utcnow()
    await db.flush()
    await db.refresh(event)
    return {"data": CalendarEventResponse.model_validate(event)}


@router.post("/gardens/{garden_id}/events/generate", response_model=dict)
async def generate_schedule(
    garden_id: int,
    planting_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement auto-schedule generation (Phase 3)
    return {"data": {"status": "not_implemented", "message": "Schedule generation coming in Phase 3"}}


@router.get("/gardens/{garden_id}/events/weather-alerts", response_model=dict)
async def weather_alerts(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement weather-responsive alerts (Phase 3)
    return {"data": []}

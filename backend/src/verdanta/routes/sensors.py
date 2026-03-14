from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.garden import Garden
from verdanta.models.weather import SensorReading
from verdanta.schemas.weather import SensorReadingCreate, SensorReadingResponse
from verdanta.services.sensor_service import (
    discover_sensors_from_db,
    get_sensor_status,
    register_sensor,
)

router = APIRouter()


@router.get("/gardens/{garden_id}/sensors", response_model=dict)
async def list_sensors(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all known sensors for a garden, discovered from readings and MQTT."""
    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    sensors = await discover_sensors_from_db(garden_id, db)
    return {"data": sensors, "count": len(sensors)}


@router.get("/gardens/{garden_id}/sensors/{sensor_id}/readings", response_model=dict)
async def sensor_readings(
    garden_id: int,
    sensor_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> dict:
    query = select(SensorReading).where(
        SensorReading.garden_id == garden_id,
        SensorReading.sensor_id == sensor_id,
    )
    if start:
        query = query.where(SensorReading.timestamp >= start)
    if end:
        query = query.where(SensorReading.timestamp <= end)
    result = await db.execute(query.order_by(SensorReading.timestamp.desc()).limit(limit))
    readings = result.scalars().all()
    validated = [SensorReadingResponse.model_validate(r) for r in readings]
    return {"data": validated, "count": len(readings)}


@router.post("/gardens/{garden_id}/sensors/reading", response_model=dict, status_code=201)
async def manual_sensor_entry(
    garden_id: int,
    reading_in: SensorReadingCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    reading = SensorReading(
        garden_id=garden_id,
        timestamp=reading_in.timestamp or datetime.now(UTC),
        **reading_in.model_dump(exclude={"timestamp"}),
    )
    db.add(reading)
    await db.flush()
    await db.refresh(reading)

    register_sensor(
        garden_id=garden_id,
        sensor_id=reading_in.sensor_id,
        sensor_type=reading_in.sensor_type,
        location=reading_in.location,
        source="manual",
    )

    return {"data": SensorReadingResponse.model_validate(reading)}


@router.get("/gardens/{garden_id}/sensors/status", response_model=dict)
async def sensor_status(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get health and status information for all sensors in a garden."""
    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    statuses = await get_sensor_status(garden_id, db)
    return {"data": statuses, "count": len(statuses)}

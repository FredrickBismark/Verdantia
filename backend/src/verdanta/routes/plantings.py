from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.garden import Garden
from verdanta.models.planting import Planting
from verdanta.schemas.planting import PlantingCreate, PlantingResponse, PlantingUpdate

router = APIRouter()


@router.get("/gardens/{garden_id}/plantings", response_model=dict)
async def list_plantings(
    garden_id: int,
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    base_query = select(Planting).where(Planting.garden_id == garden_id)
    if status:
        base_query = base_query.where(Planting.status == status)
    result = await db.execute(base_query.offset(skip).limit(limit))
    plantings = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()
    return {"data": [PlantingResponse.model_validate(p) for p in plantings], "count": total}


@router.post("/gardens/{garden_id}/plantings", response_model=dict, status_code=201)
async def create_planting(
    garden_id: int,
    planting_in: PlantingCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    data = planting_in.model_dump(exclude={"auto_generate_events"})
    planting = Planting(garden_id=garden_id, **data)
    db.add(planting)
    await db.flush()
    await db.refresh(planting)
    # TODO: auto-generate calendar events if planting_in.auto_generate_events (Phase 3)
    return {"data": PlantingResponse.model_validate(planting)}


@router.get("/plantings/{planting_id}", response_model=dict)
async def get_planting(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    planting = await db.get(Planting, planting_id)
    if not planting:
        raise HTTPException(status_code=404, detail="Planting not found")
    return {"data": PlantingResponse.model_validate(planting)}


@router.put("/plantings/{planting_id}", response_model=dict)
async def update_planting(
    planting_id: int,
    planting_in: PlantingUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    planting = await db.get(Planting, planting_id)
    if not planting:
        raise HTTPException(status_code=404, detail="Planting not found")
    for field, value in planting_in.model_dump(exclude_unset=True).items():
        setattr(planting, field, value)
    await db.flush()
    await db.refresh(planting)
    return {"data": PlantingResponse.model_validate(planting)}


@router.delete("/plantings/{planting_id}", status_code=204)
async def delete_planting(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    planting = await db.get(Planting, planting_id)
    if not planting:
        raise HTTPException(status_code=404, detail="Planting not found")
    await db.delete(planting)

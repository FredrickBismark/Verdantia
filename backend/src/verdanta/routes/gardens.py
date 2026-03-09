from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.garden import Garden
from verdanta.schemas.garden import GardenCreate, GardenResponse, GardenUpdate

router = APIRouter()


@router.get("/gardens", response_model=dict)
async def list_gardens(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Garden).offset(skip).limit(limit))
    gardens = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(Garden))
    total = count_result.scalar_one()
    return {"data": [GardenResponse.model_validate(g) for g in gardens], "count": total}


@router.post("/gardens", response_model=dict, status_code=201)
async def create_garden(
    garden_in: GardenCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    garden = Garden(**garden_in.model_dump())
    db.add(garden)
    await db.flush()
    await db.refresh(garden)
    return {"data": GardenResponse.model_validate(garden)}


@router.get("/gardens/{garden_id}", response_model=dict)
async def get_garden(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    return {"data": GardenResponse.model_validate(garden)}


@router.put("/gardens/{garden_id}", response_model=dict)
async def update_garden(
    garden_id: int,
    garden_in: GardenUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    for field, value in garden_in.model_dump(exclude_unset=True).items():
        setattr(garden, field, value)
    await db.flush()
    await db.refresh(garden)
    return {"data": GardenResponse.model_validate(garden)}


@router.delete("/gardens/{garden_id}", status_code=204)
async def delete_garden(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    await db.delete(garden)

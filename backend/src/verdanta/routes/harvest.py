from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.planting import HarvestLog
from verdanta.schemas.harvest import HarvestLogCreate, HarvestLogResponse

router = APIRouter()


@router.post("/plantings/{planting_id}/harvests", response_model=dict, status_code=201)
async def log_harvest(
    planting_id: int,
    harvest_in: HarvestLogCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    harvest = HarvestLog(planting_id=planting_id, **harvest_in.model_dump())
    db.add(harvest)
    await db.flush()
    await db.refresh(harvest)
    return {"data": HarvestLogResponse.model_validate(harvest)}


@router.get("/plantings/{planting_id}/harvests", response_model=dict)
async def list_harvests(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    base_query = select(HarvestLog).where(HarvestLog.planting_id == planting_id)
    result = await db.execute(base_query)
    harvests = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()
    return {"data": [HarvestLogResponse.model_validate(h) for h in harvests], "count": total}


@router.get("/gardens/{garden_id}/harvests/summary", response_model=dict)
async def harvest_summary(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement aggregate harvest stats (Phase 5)
    return {"data": {"total_harvests": 0, "by_plant": {}}}

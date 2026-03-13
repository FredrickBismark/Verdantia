from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.plant import PlantSpecies
from verdanta.models.planting import HarvestLog, Planting
from verdanta.schemas.harvest import HarvestLogCreate, HarvestLogResponse
from verdanta.services.knowledge_service import write_knowledge_entry

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

    # Resolve garden_id from planting for knowledge entry
    planting = await db.get(Planting, planting_id)
    garden_id = planting.garden_id if planting else None

    await write_knowledge_entry(
        db=db,
        source_type="harvest_log",
        content=(
            f"Harvested {harvest.quantity} {harvest.unit} on {harvest.harvest_date}"
            f" (quality: {harvest.quality_rating}/5)"
            if harvest.quality_rating
            else f"Harvested {harvest.quantity} {harvest.unit} on {harvest.harvest_date}"
        ),
        garden_id=garden_id,
        source_id=harvest.id,
        metadata={"planting_id": planting_id},
    )

    return {"data": HarvestLogResponse.model_validate(harvest)}


@router.get("/plantings/{planting_id}/harvests", response_model=dict)
async def list_harvests(
    planting_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    base_query = select(HarvestLog).where(HarvestLog.planting_id == planting_id)
    result = await db.execute(
        base_query.order_by(HarvestLog.harvest_date.desc()).offset(skip).limit(limit)
    )
    harvests = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()
    return {"data": [HarvestLogResponse.model_validate(h) for h in harvests], "count": total}


@router.get("/plantings/{planting_id}/harvests/stats", response_model=dict)
async def planting_harvest_stats(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(
            func.sum(HarvestLog.quantity).label("total_quantity"),
            func.avg(HarvestLog.quality_rating).label("avg_quality"),
            func.count(HarvestLog.id).label("harvest_count"),
            func.min(HarvestLog.harvest_date).label("first_harvest"),
            func.max(HarvestLog.harvest_date).label("last_harvest"),
        ).where(HarvestLog.planting_id == planting_id)
    )
    row = result.one()
    return {
        "data": {
            "planting_id": planting_id,
            "total_quantity": float(row.total_quantity) if row.total_quantity else 0,
            "avg_quality": round(float(row.avg_quality), 1) if row.avg_quality else None,
            "harvest_count": row.harvest_count,
            "first_harvest": str(row.first_harvest) if row.first_harvest else None,
            "last_harvest": str(row.last_harvest) if row.last_harvest else None,
        }
    }


@router.get("/gardens/{garden_id}/harvests/summary", response_model=dict)
async def harvest_summary(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Overall totals grouped by unit
    totals_result = await db.execute(
        select(
            HarvestLog.unit,
            func.sum(HarvestLog.quantity).label("total_quantity"),
            func.avg(HarvestLog.quality_rating).label("avg_quality"),
            func.count(HarvestLog.id).label("harvest_count"),
        )
        .join(Planting, HarvestLog.planting_id == Planting.id)
        .where(Planting.garden_id == garden_id)
        .group_by(HarvestLog.unit)
    )
    by_unit = [
        {
            "unit": row.unit,
            "total_quantity": float(row.total_quantity),
            "avg_quality": round(float(row.avg_quality), 1) if row.avg_quality else None,
            "harvest_count": row.harvest_count,
        }
        for row in totals_result.all()
    ]

    # Date range
    range_result = await db.execute(
        select(
            func.min(HarvestLog.harvest_date).label("first_harvest"),
            func.max(HarvestLog.harvest_date).label("last_harvest"),
            func.count(HarvestLog.id).label("total_count"),
        )
        .join(Planting, HarvestLog.planting_id == Planting.id)
        .where(Planting.garden_id == garden_id)
    )
    range_row = range_result.one()

    # Grouped by species
    species_result = await db.execute(
        select(
            PlantSpecies.common_name,
            HarvestLog.unit,
            func.sum(HarvestLog.quantity).label("total_quantity"),
            func.count(HarvestLog.id).label("harvest_count"),
        )
        .join(Planting, HarvestLog.planting_id == Planting.id)
        .join(PlantSpecies, Planting.species_id == PlantSpecies.id)
        .where(Planting.garden_id == garden_id)
        .group_by(PlantSpecies.common_name, HarvestLog.unit)
    )
    by_species = [
        {
            "species": row.common_name,
            "unit": row.unit,
            "total_quantity": float(row.total_quantity),
            "harvest_count": row.harvest_count,
        }
        for row in species_result.all()
    ]

    return {
        "data": {
            "garden_id": garden_id,
            "total_harvests": range_row.total_count,
            "first_harvest": str(range_row.first_harvest) if range_row.first_harvest else None,
            "last_harvest": str(range_row.last_harvest) if range_row.last_harvest else None,
            "by_unit": by_unit,
            "by_species": by_species,
        }
    }

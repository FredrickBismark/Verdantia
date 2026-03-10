import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from verdanta.core.database import get_db
from verdanta.models.plant import PlantDataSource, PlantSpecies
from verdanta.schemas.plant import (
    PlantDataSourceResponse,
    PlantDetailResponse,
    PlantSpeciesCreate,
    PlantSpeciesResponse,
    PlantSpeciesUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/plants", response_model=dict)
async def list_plants(
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    growth_habit: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    query = select(PlantSpecies)
    if search:
        query = query.where(PlantSpecies.common_name.ilike(f"%{search}%"))
    if growth_habit:
        query = query.where(PlantSpecies.growth_habit == growth_habit)
    result = await db.execute(query.offset(skip).limit(limit))
    plants = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()
    return {"data": [PlantSpeciesResponse.model_validate(p) for p in plants], "count": total}


@router.post("/plants", response_model=dict, status_code=201)
async def create_plant(
    plant_in: PlantSpeciesCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    plant = PlantSpecies(**plant_in.model_dump())
    db.add(plant)
    await db.flush()
    await db.refresh(plant)
    return {"data": PlantSpeciesResponse.model_validate(plant)}


@router.get("/plants/{plant_id}", response_model=dict)
async def get_plant(
    plant_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(PlantSpecies)
        .where(PlantSpecies.id == plant_id)
        .options(
            selectinload(PlantSpecies.dossier_sections),
            selectinload(PlantSpecies.data_sources),
        )
    )
    plant = result.scalar_one_or_none()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return {"data": PlantDetailResponse.model_validate(plant)}


@router.put("/plants/{plant_id}", response_model=dict)
async def update_plant(
    plant_id: int,
    plant_in: PlantSpeciesUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    plant = await db.get(PlantSpecies, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    for field, value in plant_in.model_dump(exclude_unset=True).items():
        setattr(plant, field, value)
    await db.flush()
    await db.refresh(plant)
    return {"data": PlantSpeciesResponse.model_validate(plant)}


@router.delete("/plants/{plant_id}", status_code=204)
async def delete_plant(
    plant_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    plant = await db.get(PlantSpecies, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    await db.delete(plant)


@router.post("/plants/{plant_id}/curate", response_model=dict)
async def curate_plant(
    plant_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    plant = await db.get(PlantSpecies, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    try:
        from verdanta.services.plant_curation_service import (
            curate_plant as run_curation,
        )

        await run_curation(plant_id, db)
        # Reload with relationships
        result = await db.execute(
            select(PlantSpecies)
            .where(PlantSpecies.id == plant_id)
            .options(
                selectinload(PlantSpecies.dossier_sections),
                selectinload(PlantSpecies.data_sources),
            )
        )
        plant_detail = result.scalar_one()
        return {"data": PlantDetailResponse.model_validate(plant_detail)}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Curation failed for plant %d", plant_id)
        raise HTTPException(
            status_code=502, detail="Curation failed — check LLM provider settings"
        ) from exc


@router.get("/plants/{plant_id}/sources", response_model=dict)
async def get_plant_sources(
    plant_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    base_query = select(PlantDataSource).where(PlantDataSource.species_id == plant_id)
    result = await db.execute(base_query.offset(skip).limit(limit))
    sources = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()
    return {"data": [PlantDataSourceResponse.model_validate(s) for s in sources], "count": total}

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.soil import SoilTest
from verdanta.schemas.soil import SoilTestCreate, SoilTestResponse

router = APIRouter()


@router.post("/gardens/{garden_id}/soil-tests", response_model=dict, status_code=201)
async def record_soil_test(
    garden_id: int,
    test_in: SoilTestCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    soil_test = SoilTest(garden_id=garden_id, **test_in.model_dump())
    db.add(soil_test)
    await db.flush()
    await db.refresh(soil_test)
    return {"data": SoilTestResponse.model_validate(soil_test)}


@router.get("/gardens/{garden_id}/soil-tests", response_model=dict)
async def list_soil_tests(
    garden_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    base_query = select(SoilTest).where(SoilTest.garden_id == garden_id)
    result = await db.execute(base_query.offset(skip).limit(limit))
    tests = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()
    return {"data": [SoilTestResponse.model_validate(t) for t in tests], "count": total}

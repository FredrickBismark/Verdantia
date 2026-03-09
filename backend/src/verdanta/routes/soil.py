from fastapi import APIRouter, Depends
from sqlalchemy import select
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
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(SoilTest).where(SoilTest.garden_id == garden_id))
    tests = result.scalars().all()
    return {"data": [SoilTestResponse.model_validate(t) for t in tests], "count": len(tests)}

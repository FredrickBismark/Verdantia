from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.planting import Photo
from verdanta.schemas.photo import PhotoResponse

router = APIRouter()


@router.post("/plantings/{planting_id}/photos", response_model=dict, status_code=201)
async def upload_photo(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement photo upload with multipart form (Phase 5)
    raise HTTPException(status_code=501, detail="Photo upload not yet implemented")


@router.get("/plantings/{planting_id}/photos", response_model=dict)
async def list_photos(
    planting_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    base_query = select(Photo).where(Photo.planting_id == planting_id)
    result = await db.execute(base_query.offset(skip).limit(limit))
    photos = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()
    return {"data": [PhotoResponse.model_validate(p) for p in photos], "count": total}


@router.get("/photos/{photo_id}", response_model=dict)
async def get_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    photo = await db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return {"data": PhotoResponse.model_validate(photo)}


@router.delete("/photos/{photo_id}", status_code=204)
async def delete_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    photo = await db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    # TODO: Delete file from disk (Phase 5)
    await db.delete(photo)

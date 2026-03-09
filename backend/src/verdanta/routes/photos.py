from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.planting import Photo

router = APIRouter()


@router.post("/plantings/{planting_id}/photos", response_model=dict, status_code=201)
async def upload_photo(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement photo upload with multipart form (Phase 5)
    return {"data": {"status": "not_implemented"}}


@router.get("/plantings/{planting_id}/photos", response_model=dict)
async def list_photos(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Photo).where(Photo.planting_id == planting_id))
    photos = result.scalars().all()
    return {"data": photos, "count": len(photos)}


@router.get("/photos/{photo_id}", response_model=dict)
async def get_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    photo = await db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return {"data": photo}


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

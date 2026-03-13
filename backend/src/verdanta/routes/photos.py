from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.planting import Photo, Planting
from verdanta.schemas.photo import PhotoResponse
from verdanta.services.photo_service import delete_photo_files, save_photo

router = APIRouter()


@router.post("/plantings/{planting_id}/photos", response_model=dict, status_code=201)
async def upload_photo(
    planting_id: int,
    file: UploadFile,
    caption: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    planting = await db.get(Planting, planting_id)
    if not planting:
        raise HTTPException(status_code=404, detail="Planting not found")

    try:
        result = await save_photo(
            file=file,
            garden_id=planting.garden_id,
            planting_id=planting_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    photo = Photo(
        planting_id=planting_id,
        garden_id=planting.garden_id,
        file_path=result["file_path"],
        thumbnail_path=result["thumbnail_path"],
        caption=caption,
        taken_at=result["taken_at"],
    )
    db.add(photo)
    await db.flush()
    await db.refresh(photo)
    return {"data": PhotoResponse.model_validate(photo)}


@router.get("/plantings/{planting_id}/photos", response_model=dict)
async def list_photos(
    planting_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    base_query = select(Photo).where(Photo.planting_id == planting_id)
    result = await db.execute(
        base_query.order_by(Photo.taken_at.desc()).offset(skip).limit(limit)
    )
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


@router.get("/photos/{photo_id}/file")
async def get_photo_file(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    photo = await db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    path = Path(photo.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo file not found on disk")
    return FileResponse(path)


@router.get("/photos/{photo_id}/thumbnail")
async def get_photo_thumbnail(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    photo = await db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    thumb = photo.thumbnail_path
    if not thumb or not Path(thumb).exists():
        path = Path(photo.file_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Photo file not found on disk")
        return FileResponse(path)
    return FileResponse(thumb)


@router.delete("/photos/{photo_id}", status_code=204)
async def delete_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    photo = await db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    delete_photo_files(photo.file_path, photo.thumbnail_path)
    await db.delete(photo)

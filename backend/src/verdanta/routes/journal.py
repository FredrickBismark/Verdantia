from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.journal import JournalEntry
from verdanta.schemas.journal import JournalEntryCreate, JournalEntryResponse, JournalEntryUpdate

router = APIRouter()


@router.post("/gardens/{garden_id}/journal", response_model=dict, status_code=201)
async def create_journal_entry(
    garden_id: int,
    entry_in: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    entry = JournalEntry(garden_id=garden_id, **entry_in.model_dump())
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return {"data": JournalEntryResponse.model_validate(entry)}


@router.get("/gardens/{garden_id}/journal", response_model=dict)
async def list_journal_entries(
    garden_id: int,
    skip: int = 0,
    limit: int = 20,
    planting_id: int | None = None,
    category: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    query = select(JournalEntry).where(JournalEntry.garden_id == garden_id)
    if planting_id is not None:
        query = query.where(JournalEntry.planting_id == planting_id)
    if category:
        query = query.where(JournalEntry.category == category)
    if start_date:
        query = query.where(JournalEntry.entry_date >= start_date)
    if end_date:
        query = query.where(JournalEntry.entry_date <= end_date)
    if tag:
        query = query.where(JournalEntry.tags.contains(tag))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    entries = result.scalars().all()
    return {"data": [JournalEntryResponse.model_validate(e) for e in entries], "count": total}


@router.get("/gardens/{garden_id}/journal/recent", response_model=dict)
async def recent_journal_entries(
    garden_id: int,
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(JournalEntry)
        .where(JournalEntry.garden_id == garden_id)
        .order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
        .limit(limit)
    )
    entries = result.scalars().all()
    return {
        "data": [JournalEntryResponse.model_validate(e) for e in entries],
        "count": len(entries),
    }


@router.get("/journal/{entry_id}", response_model=dict)
async def get_journal_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    entry = await db.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return {"data": JournalEntryResponse.model_validate(entry)}


@router.put("/journal/{entry_id}", response_model=dict)
async def update_journal_entry(
    entry_id: int,
    entry_in: JournalEntryUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    entry = await db.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    update_data = entry_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(entry, key, value)
    await db.flush()
    await db.refresh(entry)
    return {"data": JournalEntryResponse.model_validate(entry)}


@router.delete("/journal/{entry_id}", status_code=204)
async def delete_journal_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    entry = await db.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    await db.delete(entry)

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class JournalEntryCreate(BaseModel):
    planting_id: int | None = None
    entry_date: date
    category: str
    content: str
    tags: list[str] | None = None
    mood: str | None = None


class JournalEntryUpdate(BaseModel):
    planting_id: int | None = None
    entry_date: date | None = None
    category: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    mood: str | None = None


class JournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    garden_id: int
    planting_id: int | None
    entry_date: date
    category: str
    content: str
    tags: list[str] | None
    mood: str | None
    created_at: datetime
    updated_at: datetime

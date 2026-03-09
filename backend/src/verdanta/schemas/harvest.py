from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class HarvestLogCreate(BaseModel):
    harvest_date: date
    quantity: float
    unit: str
    quality_rating: int | None = None
    notes: str | None = None


class HarvestLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    planting_id: int
    harvest_date: date
    quantity: float
    unit: str
    quality_rating: int | None
    notes: str | None
    created_at: datetime

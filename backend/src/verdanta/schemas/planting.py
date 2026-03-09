from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PlantingBase(BaseModel):
    species_id: int
    bed_or_location: str | None = None
    quantity: int = 1
    date_seeded: date | None = None
    date_transplanted: date | None = None
    date_first_harvest: date | None = None
    date_last_harvest: date | None = None
    date_removed: date | None = None
    status: str = "planned"
    notes: str | None = None
    custom_fields: dict | None = None


class PlantingCreate(PlantingBase):
    auto_generate_events: bool = False


class PlantingUpdate(BaseModel):
    species_id: int | None = None
    bed_or_location: str | None = None
    quantity: int | None = None
    date_seeded: date | None = None
    date_transplanted: date | None = None
    date_first_harvest: date | None = None
    date_last_harvest: date | None = None
    date_removed: date | None = None
    status: str | None = None
    notes: str | None = None
    custom_fields: dict | None = None


class PlantingResponse(PlantingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    garden_id: int
    created_at: datetime
    updated_at: datetime

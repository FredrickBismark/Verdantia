from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class SoilTestCreate(BaseModel):
    location: str | None = None
    test_date: date
    ph: float | None = None
    nitrogen_ppm: float | None = None
    phosphorus_ppm: float | None = None
    potassium_ppm: float | None = None
    organic_matter_pct: float | None = None
    texture: str | None = None
    notes: str | None = None
    raw_data: dict | None = None


class SoilTestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    garden_id: int
    location: str | None
    test_date: date
    ph: float | None
    nitrogen_ppm: float | None
    phosphorus_ppm: float | None
    potassium_ppm: float | None
    organic_matter_pct: float | None
    texture: str | None
    notes: str | None
    raw_data: dict | None
    created_at: datetime

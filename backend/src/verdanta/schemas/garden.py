from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GardenBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    elevation_m: float | None = None
    usda_zone: str | None = None
    soil_type_default: str | None = None
    timezone: str = "UTC"
    notes: str | None = None


class GardenCreate(GardenBase):
    pass


class GardenUpdate(BaseModel):
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    elevation_m: float | None = None
    usda_zone: str | None = None
    soil_type_default: str | None = None
    timezone: str | None = None
    notes: str | None = None


class GardenResponse(GardenBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

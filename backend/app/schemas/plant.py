from datetime import datetime

from pydantic import BaseModel


class PlantBase(BaseModel):
    name: str
    species: str | None = None
    variety: str | None = None
    description: str | None = None
    care_notes: str | None = None
    sun_requirement: str | None = None
    water_requirement: str | None = None
    soil_type: str | None = None
    garden_id: int | None = None


class PlantCreate(PlantBase):
    pass


class PlantUpdate(BaseModel):
    name: str | None = None
    species: str | None = None
    variety: str | None = None
    description: str | None = None
    care_notes: str | None = None
    sun_requirement: str | None = None
    water_requirement: str | None = None
    soil_type: str | None = None
    garden_id: int | None = None


class PlantRead(PlantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

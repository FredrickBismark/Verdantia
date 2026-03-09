from datetime import datetime

from pydantic import BaseModel


class GardenBase(BaseModel):
    name: str
    location: str | None = None
    description: str | None = None
    hardiness_zone: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class GardenCreate(GardenBase):
    pass


class GardenUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    description: str | None = None
    hardiness_zone: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class GardenRead(GardenBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

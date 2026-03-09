from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class WeatherRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    garden_id: int
    timestamp: datetime
    record_type: str
    source: str
    temp_c: float | None
    temp_min_c: float | None
    temp_max_c: float | None
    humidity_pct: float | None
    precipitation_mm: float | None
    wind_speed_kmh: float | None
    soil_temp_c: float | None
    soil_moisture_pct: float | None
    uv_index: float | None
    cloud_cover_pct: float | None
    frost_risk: bool | None
    sensor_id: str | None
    raw_data: dict[str, Any] | None
    fetched_at: datetime


class SensorReadingCreate(BaseModel):
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime | None = None
    location: str | None = None


class SensorReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    garden_id: int
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime
    location: str | None

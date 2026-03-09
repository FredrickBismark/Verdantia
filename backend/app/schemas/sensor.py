from datetime import datetime

from pydantic import BaseModel


class SensorReadingBase(BaseModel):
    sensor_id: str
    metric: str
    value: float
    unit: str
    recorded_at: datetime
    garden_id: int | None = None


class SensorReadingCreate(SensorReadingBase):
    pass


class SensorReadingRead(SensorReadingBase):
    id: int

    model_config = {"from_attributes": True}

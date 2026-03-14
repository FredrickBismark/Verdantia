from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AlertCreate(BaseModel):
    alert_type: str
    severity: str = "medium"
    title: str
    description: str | None = None
    trigger_date: date
    planting_id: int | None = None
    source: str = "manual"
    metadata_json: dict | None = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    garden_id: int
    planting_id: int | None
    alert_type: str
    severity: str
    title: str
    description: str | None
    source: str
    trigger_date: date
    triggered_at: datetime
    acknowledged: bool
    acknowledged_at: datetime | None
    dismissed: bool
    dismissed_at: datetime | None
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


class CalendarEventBase(BaseModel):
    planting_id: int | None = None
    event_type: str
    title: str
    description: str | None = None
    scheduled_date: date
    scheduled_time: time | None = None
    recurrence_rule: str | None = None
    source: str = "manual"
    priority: str | None = None
    weather_dependent: bool = False
    color: str | None = None


class CalendarEventCreate(CalendarEventBase):
    pass


class CalendarEventUpdate(BaseModel):
    planting_id: int | None = None
    event_type: str | None = None
    title: str | None = None
    description: str | None = None
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    recurrence_rule: str | None = None
    priority: str | None = None
    weather_dependent: bool | None = None
    color: str | None = None


class CalendarEventResponse(CalendarEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    garden_id: int
    completed: bool
    completed_at: datetime | None
    created_at: datetime

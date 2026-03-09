from datetime import date, datetime

from pydantic import BaseModel


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    task_type: str
    status: str = "pending"
    due_date: date | None = None
    plant_id: int | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    task_type: str | None = None
    status: str | None = None
    due_date: date | None = None
    completed_at: datetime | None = None
    plant_id: int | None = None


class TaskRead(TaskBase):
    id: int
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

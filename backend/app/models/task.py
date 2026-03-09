from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(50))  # water, fertilize, prune, harvest, etc.
    status: Mapped[str] = mapped_column(String(20), default="pending")
    due_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    plant_id: Mapped[int | None] = mapped_column(ForeignKey("plants.id"))
    plant: Mapped["Plant | None"] = relationship(back_populates="tasks")  # noqa: F821

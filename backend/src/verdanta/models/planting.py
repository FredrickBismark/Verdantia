from datetime import date, datetime, time

from sqlalchemy import JSON, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verdanta.models.base import Base


class Planting(Base):
    __tablename__ = "plantings"

    id: Mapped[int] = mapped_column(primary_key=True)
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    species_id: Mapped[int] = mapped_column(ForeignKey("plant_species.id"))
    bed_or_location: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(default=1)
    date_seeded: Mapped[date | None]
    date_transplanted: Mapped[date | None]
    date_first_harvest: Mapped[date | None]
    date_last_harvest: Mapped[date | None]
    date_removed: Mapped[date | None]
    status: Mapped[str] = mapped_column(String(50), default="planned")
    notes: Mapped[str | None] = mapped_column(Text)
    custom_fields: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    garden: Mapped["Garden"] = relationship(back_populates="plantings")  # noqa: F821
    species: Mapped["PlantSpecies"] = relationship(back_populates="plantings")  # noqa: F821
    calendar_events: Mapped[list["CalendarEvent"]] = relationship(back_populates="planting")
    photos: Mapped[list["Photo"]] = relationship(
        back_populates="planting", cascade="all, delete-orphan"
    )
    harvest_logs: Mapped[list["HarvestLog"]] = relationship(
        back_populates="planting", cascade="all, delete-orphan"
    )


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    planting_id: Mapped[int | None] = mapped_column(ForeignKey("plantings.id"))
    event_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    scheduled_date: Mapped[date]
    scheduled_time: Mapped[time | None]
    recurrence_rule: Mapped[str | None] = mapped_column(String(255))
    completed: Mapped[bool] = mapped_column(default=False)
    completed_at: Mapped[datetime | None]
    source: Mapped[str] = mapped_column(String(50), default="manual")
    priority: Mapped[str | None] = mapped_column(String(20))
    weather_dependent: Mapped[bool] = mapped_column(default=False)
    color: Mapped[str | None] = mapped_column(String(7))
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    garden: Mapped["Garden"] = relationship(back_populates="calendar_events")  # noqa: F821
    planting: Mapped["Planting | None"] = relationship(back_populates="calendar_events")


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    planting_id: Mapped[int | None] = mapped_column(ForeignKey("plantings.id"))
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    file_path: Mapped[str] = mapped_column(String(500))
    thumbnail_path: Mapped[str | None] = mapped_column(String(500))
    caption: Mapped[str | None] = mapped_column(Text)
    taken_at: Mapped[datetime]
    tags: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    planting: Mapped["Planting | None"] = relationship(back_populates="photos")


class HarvestLog(Base):
    __tablename__ = "harvest_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    planting_id: Mapped[int] = mapped_column(ForeignKey("plantings.id"))
    harvest_date: Mapped[date]
    quantity: Mapped[float]
    unit: Mapped[str] = mapped_column(String(20))
    quality_rating: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    planting: Mapped["Planting"] = relationship(back_populates="harvest_logs")

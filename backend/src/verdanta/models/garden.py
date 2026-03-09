from datetime import datetime

from sqlalchemy import JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verdanta.models.base import Base


class Garden(Base):
    __tablename__ = "gardens"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float]
    longitude: Mapped[float]
    elevation_m: Mapped[float | None]
    usda_zone: Mapped[str | None] = mapped_column(String(10))
    soil_type_default: Mapped[str | None] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    plantings: Mapped[list["Planting"]] = relationship(  # noqa: F821
        back_populates="garden", cascade="all, delete-orphan"
    )
    calendar_events: Mapped[list["CalendarEvent"]] = relationship(  # noqa: F821
        back_populates="garden", cascade="all, delete-orphan"
    )
    weather_records: Mapped[list["WeatherRecord"]] = relationship(  # noqa: F821
        back_populates="garden", cascade="all, delete-orphan"
    )
    sensor_readings: Mapped[list["SensorReading"]] = relationship(  # noqa: F821
        back_populates="garden", cascade="all, delete-orphan"
    )
    soil_tests: Mapped[list["SoilTest"]] = relationship(  # noqa: F821
        back_populates="garden", cascade="all, delete-orphan"
    )

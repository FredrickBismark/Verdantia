from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verdanta.models.base import Base


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    timestamp: Mapped[datetime]
    record_type: Mapped[str] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(50))
    sensor_id: Mapped[str | None] = mapped_column(String(100))
    temp_c: Mapped[float | None]
    temp_min_c: Mapped[float | None]
    temp_max_c: Mapped[float | None]
    humidity_pct: Mapped[float | None]
    precipitation_mm: Mapped[float | None]
    wind_speed_kmh: Mapped[float | None]
    soil_temp_c: Mapped[float | None]
    soil_moisture_pct: Mapped[float | None]
    uv_index: Mapped[float | None]
    cloud_cover_pct: Mapped[float | None]
    frost_risk: Mapped[bool | None]
    raw_data: Mapped[dict | None] = mapped_column(JSON)
    fetched_at: Mapped[datetime] = mapped_column(default=func.now())

    garden: Mapped["Garden"] = relationship(back_populates="weather_records")  # noqa: F821


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    sensor_id: Mapped[str] = mapped_column(String(100))
    sensor_type: Mapped[str] = mapped_column(String(50))
    value: Mapped[float]
    unit: Mapped[str] = mapped_column(String(20))
    timestamp: Mapped[datetime]
    location: Mapped[str | None] = mapped_column(String(255))

    garden: Mapped["Garden"] = relationship(back_populates="sensor_readings")  # noqa: F821

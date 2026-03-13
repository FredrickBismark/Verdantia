from datetime import date, datetime

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verdanta.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    planting_id: Mapped[int | None] = mapped_column(ForeignKey("plantings.id"))
    alert_type: Mapped[str] = mapped_column(String(50))
    # alert_type: frost, extreme_weather, watering, pest, disease, harvest, general
    severity: Mapped[str] = mapped_column(String(20))
    # severity: low, medium, high, critical
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), default="system")
    # source: weather_service, llm_analysis, calendar, sensor, manual
    trigger_date: Mapped[date]
    triggered_at: Mapped[datetime] = mapped_column(default=func.now())
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[datetime | None]
    dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissed_at: Mapped[datetime | None]
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    garden: Mapped["Garden"] = relationship(back_populates="alerts")  # noqa: F821
    planting: Mapped["Planting | None"] = relationship(back_populates="alerts")  # noqa: F821

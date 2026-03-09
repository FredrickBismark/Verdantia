from datetime import date, datetime

from sqlalchemy import JSON, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verdanta.models.base import Base


class SoilTest(Base):
    __tablename__ = "soil_tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    location: Mapped[str | None] = mapped_column(String(255))
    test_date: Mapped[date]
    ph: Mapped[float | None]
    nitrogen_ppm: Mapped[float | None]
    phosphorus_ppm: Mapped[float | None]
    potassium_ppm: Mapped[float | None]
    organic_matter_pct: Mapped[float | None]
    texture: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    garden: Mapped["Garden"] = relationship(back_populates="soil_tests")  # noqa: F821

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Plant(Base, TimestampMixin):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200))
    species: Mapped[str | None] = mapped_column(String(200))
    variety: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    care_notes: Mapped[str | None] = mapped_column(Text)
    sun_requirement: Mapped[str | None] = mapped_column(String(50))
    water_requirement: Mapped[str | None] = mapped_column(String(50))
    soil_type: Mapped[str | None] = mapped_column(String(100))

    garden_id: Mapped[int | None] = mapped_column(ForeignKey("gardens.id"))
    garden: Mapped["Garden | None"] = relationship(back_populates="plants")  # noqa: F821

    tasks: Mapped[list["Task"]] = relationship(back_populates="plant")  # noqa: F821

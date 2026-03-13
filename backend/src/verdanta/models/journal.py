from datetime import date, datetime

from sqlalchemy import JSON, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verdanta.models.base import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    planting_id: Mapped[int | None] = mapped_column(ForeignKey("plantings.id"))
    entry_date: Mapped[date]
    category: Mapped[str] = mapped_column(String(50))
    # categories: observation, pest_issue, disease_issue, milestone,
    # weather_note, soil_note, general, harvest_note
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[list | None] = mapped_column(JSON)
    mood: Mapped[str | None] = mapped_column(String(20))
    # mood: great, good, okay, concerned, bad (optional gardener sentiment)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    garden: Mapped["Garden"] = relationship(back_populates="journal_entries")  # noqa: F821
    planting: Mapped["Planting | None"] = relationship(back_populates="journal_entries")  # noqa: F821

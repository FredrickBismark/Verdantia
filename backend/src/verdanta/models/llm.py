from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verdanta.models.base import Base


class LLMInteraction(Base):
    __tablename__ = "llm_interactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    garden_id: Mapped[int | None] = mapped_column(ForeignKey("gardens.id"), nullable=True)
    planting_id: Mapped[int | None] = mapped_column(ForeignKey("plantings.id"))
    interaction_type: Mapped[str] = mapped_column(String(50))
    user_prompt: Mapped[str] = mapped_column(Text)
    system_context: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    model_used: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="completed")
    error_message: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None]
    timestamp: Mapped[datetime] = mapped_column(default=func.now())
    feedback: Mapped[str | None] = mapped_column(String(20))
    tokens_used: Mapped[int | None]

    garden: Mapped["Garden | None"] = relationship(back_populates="llm_interactions")  # noqa: F821
    planting: Mapped["Planting | None"] = relationship()  # noqa: F821

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verdanta.models.base import Base


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    garden_id: Mapped[int | None] = mapped_column(ForeignKey("gardens.id"))
    source_type: Mapped[str] = mapped_column(String(50))
    # source_type: journal_entry, advisor_conversation, dossier_section,
    # harvest_log, weather_summary, observation, planting_lifecycle
    source_id: Mapped[int | None]
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    # metadata: planting_id, species_name, date_range, category, etc.
    embedding_vector: Mapped[str | None] = mapped_column(Text)
    # nullable — will store serialized vector when embedding model is added
    chunk_index: Mapped[int] = mapped_column(default=0)
    # for sources that produce multiple chunks
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    garden: Mapped["Garden | None"] = relationship()  # noqa: F821

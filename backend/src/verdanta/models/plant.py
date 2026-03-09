from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verdanta.models.base import Base


class PlantSpecies(Base):
    __tablename__ = "plant_species"

    id: Mapped[int] = mapped_column(primary_key=True)
    common_name: Mapped[str] = mapped_column(String(255))
    scientific_name: Mapped[str | None] = mapped_column(String(255))
    family: Mapped[str | None] = mapped_column(String(100))
    variety: Mapped[str | None] = mapped_column(String(255))
    growth_habit: Mapped[str | None] = mapped_column(String(50))
    days_to_maturity_min: Mapped[int | None]
    days_to_maturity_max: Mapped[int | None]
    optimal_soil_ph_min: Mapped[float | None]
    optimal_soil_ph_max: Mapped[float | None]
    sun_requirement: Mapped[str | None] = mapped_column(String(50))
    water_requirement: Mapped[str | None] = mapped_column(String(50))
    frost_tolerance: Mapped[str | None] = mapped_column(String(50))
    min_temp_c: Mapped[float | None]
    max_temp_c: Mapped[float | None]
    spacing_cm: Mapped[int | None]
    depth_cm: Mapped[int | None]
    companion_plants: Mapped[dict | None] = mapped_column(JSON)
    antagonist_plants: Mapped[dict | None] = mapped_column(JSON)

    # LLM curation metadata
    curation_status: Mapped[str] = mapped_column(String(50), default="raw")
    last_curated_at: Mapped[datetime | None]
    curation_model: Mapped[str | None] = mapped_column(String(100))

    custom_fields: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    # Relationships
    plantings: Mapped[list["Planting"]] = relationship(back_populates="species")  # noqa: F821
    data_sources: Mapped[list["PlantDataSource"]] = relationship(
        back_populates="species", cascade="all, delete-orphan"
    )
    dossier_sections: Mapped[list["DossierSection"]] = relationship(
        back_populates="species", cascade="all, delete-orphan"
    )


class PlantDataSource(Base):
    __tablename__ = "plant_data_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("plant_species.id"))
    source_type: Mapped[str] = mapped_column(String(50))
    source_name: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict] = mapped_column(JSON)
    confidence_score: Mapped[float | None]
    ingested_at: Mapped[datetime] = mapped_column(default=func.now())
    notes: Mapped[str | None] = mapped_column(Text)

    species: Mapped["PlantSpecies"] = relationship(back_populates="data_sources")


class DossierSection(Base):
    __tablename__ = "dossier_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("plant_species.id"))
    section_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(20))
    source_ids: Mapped[list | None] = mapped_column(JSON)
    display_order: Mapped[int] = mapped_column(default=0)
    is_localized: Mapped[bool] = mapped_column(default=False)
    last_updated: Mapped[datetime] = mapped_column(default=func.now())

    species: Mapped["PlantSpecies"] = relationship(back_populates="dossier_sections")

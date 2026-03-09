from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PlantSpeciesBase(BaseModel):
    common_name: str
    scientific_name: str | None = None
    family: str | None = None
    variety: str | None = None
    growth_habit: str | None = None
    days_to_maturity_min: int | None = None
    days_to_maturity_max: int | None = None
    optimal_soil_ph_min: float | None = None
    optimal_soil_ph_max: float | None = None
    sun_requirement: str | None = None
    water_requirement: str | None = None
    frost_tolerance: str | None = None
    min_temp_c: float | None = None
    max_temp_c: float | None = None
    spacing_cm: int | None = None
    depth_cm: int | None = None
    companion_plants: dict[str, Any] | None = None
    antagonist_plants: dict[str, Any] | None = None
    custom_fields: dict[str, Any] | None = None


class PlantSpeciesCreate(PlantSpeciesBase):
    pass


class PlantSpeciesUpdate(BaseModel):
    common_name: str | None = None
    scientific_name: str | None = None
    family: str | None = None
    variety: str | None = None
    growth_habit: str | None = None
    days_to_maturity_min: int | None = None
    days_to_maturity_max: int | None = None
    optimal_soil_ph_min: float | None = None
    optimal_soil_ph_max: float | None = None
    sun_requirement: str | None = None
    water_requirement: str | None = None
    frost_tolerance: str | None = None
    min_temp_c: float | None = None
    max_temp_c: float | None = None
    spacing_cm: int | None = None
    depth_cm: int | None = None
    companion_plants: dict[str, Any] | None = None
    antagonist_plants: dict[str, Any] | None = None
    custom_fields: dict[str, Any] | None = None


class PlantSpeciesResponse(PlantSpeciesBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    curation_status: str
    last_curated_at: datetime | None
    curation_model: str | None
    created_at: datetime
    updated_at: datetime


class DossierSectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    species_id: int
    section_type: str
    title: str
    content: str
    confidence: str
    source_ids: list[int] | None
    display_order: int
    is_localized: bool
    last_updated: datetime


class PlantDataSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    species_id: int
    source_type: str
    source_name: str
    source_url: str | None
    raw_data: dict[str, Any]
    confidence_score: float | None
    ingested_at: datetime
    notes: str | None


class PlantDetailResponse(PlantSpeciesResponse):
    dossier_sections: list[DossierSectionResponse] = []
    data_sources: list[PlantDataSourceResponse] = []

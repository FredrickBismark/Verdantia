"""Tests for the plant curation pipeline with mocked LLM and OpenFarm."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.models.plant import DossierSection, PlantSpecies
from verdanta.services.plant_curation_service import PlantCurationService


async def test_build_curation_prompt(db_session: AsyncSession):
    species = PlantSpecies(
        common_name="Tomato",
        scientific_name="Solanum lycopersicum",
        family="Solanaceae",
        growth_habit="Annual",
    )
    db_session.add(species)
    await db_session.flush()

    service = PlantCurationService(db_session)
    prompt = service._build_curation_prompt(species, [])

    assert "Tomato" in prompt
    assert "Solanum lycopersicum" in prompt
    assert "Solanaceae" in prompt
    assert "overview" in prompt
    assert "companion_planting" in prompt


async def test_apply_enriched_data(db_session: AsyncSession):
    species = PlantSpecies(common_name="Basil")
    db_session.add(species)
    await db_session.flush()

    service = PlantCurationService(db_session)
    parsed = {
        "enriched_data": {
            "sun_requirement": "Full Sun",
            "water_requirement": "Moderate",
            "spacing_cm": 30,
            "days_to_maturity_min": 60,
            "days_to_maturity_max": 90,
        }
    }
    service._apply_enriched_data(species, parsed)

    assert species.sun_requirement == "Full Sun"
    assert species.water_requirement == "Moderate"
    assert species.spacing_cm == 30
    assert species.days_to_maturity_min == 60
    assert species.days_to_maturity_max == 90


async def test_store_dossier_sections(db_session: AsyncSession):
    species = PlantSpecies(common_name="Pepper")
    db_session.add(species)
    await db_session.flush()

    service = PlantCurationService(db_session)
    parsed = {
        "sections": [
            {
                "section_type": "overview",
                "title": "Overview",
                "content": "Peppers are warm-season crops.",
                "confidence": "high",
            },
            {
                "section_type": "growing_conditions",
                "title": "Growing Conditions",
                "content": "Full sun, well-drained soil.",
                "confidence": "medium",
            },
        ]
    }
    await service._store_dossier_sections(species, parsed, [])
    await db_session.flush()

    result = await db_session.execute(
        select(DossierSection).where(DossierSection.species_id == species.id)
    )
    sections = result.scalars().all()
    assert len(sections) == 2
    assert sections[0].section_type == "overview"
    assert sections[0].confidence == "high"
    assert sections[1].section_type == "growing_conditions"


async def test_curate_species_full_pipeline(db_session: AsyncSession):
    """Test the full curation pipeline with mocked external calls."""
    species = PlantSpecies(common_name="Tomato", curation_status="raw")
    db_session.add(species)
    await db_session.flush()

    llm_response_data = json.dumps({
        "sections": [
            {
                "section_type": "overview",
                "title": "Overview",
                "content": "Tomato is a warm-season vegetable.",
                "confidence": "high",
            }
        ],
        "enriched_data": {
            "sun_requirement": "Full Sun",
            "days_to_maturity_min": 60,
            "days_to_maturity_max": 85,
        },
    })

    mock_llm_response = MagicMock()
    mock_llm_response.text = llm_response_data
    mock_llm_response.model = "test-model"
    mock_llm_response.provider = "ollama"

    with (
        patch.object(
            PlantCurationService, "_build_curation_prompt", return_value="test prompt"
        ),
        patch(
            "verdanta.services.plant_curation_service.OpenFarmService"
        ) as mock_openfarm_cls,
        patch(
            "verdanta.services.plant_curation_service.LLMService"
        ) as mock_llm_cls,
    ):
        mock_openfarm = AsyncMock()
        mock_openfarm.ingest_for_species = AsyncMock(return_value=None)
        mock_openfarm_cls.return_value = mock_openfarm

        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=mock_llm_response)
        mock_llm_cls.return_value = mock_llm

        service = PlantCurationService(db_session)

        result = await service.curate_species(species.id)

        assert result.curation_status == "curated"
        assert result.curation_model == "test-model"
        assert result.sun_requirement == "Full Sun"
        assert result.days_to_maturity_min == 60

        # Check dossier sections were created
        sections_result = await db_session.execute(
            select(DossierSection).where(DossierSection.species_id == species.id)
        )
        sections = sections_result.scalars().all()
        assert len(sections) == 1
        assert sections[0].content == "Tomato is a warm-season vegetable."

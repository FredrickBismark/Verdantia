from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.settings import AppSettings
from verdanta.schemas.settings import LLMTestRequest, SettingResponse, SettingUpdate

router = APIRouter()

PROVIDER_PRESETS = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "requires_api_key": False,
        "models": [
            {"id": "llama3:8b", "name": "Llama 3 8B", "vision": False},
            {"id": "llama3.1:8b", "name": "Llama 3.1 8B", "vision": False},
            {"id": "mistral:7b", "name": "Mistral 7B", "vision": False},
            {"id": "gemma2:9b", "name": "Gemma 2 9B", "vision": False},
            {"id": "llava:13b", "name": "LLaVA 13B (Vision)", "vision": True},
        ],
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "requires_api_key": True,
        "models": [
            {"id": "claude-opus-4-20250514", "name": "Claude Opus 4", "vision": True},
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "vision": True},
            {"id": "claude-haiku-3", "name": "Claude Haiku 3", "vision": True},
        ],
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "requires_api_key": True,
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "vision": True},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "vision": True},
        ],
    },
    "venice": {
        "base_url": "https://api.venice.ai/api/v1",
        "requires_api_key": True,
        "models": [
            {"id": "llama-3.3-70b", "name": "Llama 3.3 70B", "vision": False},
        ],
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "requires_api_key": True,
        "models": [],
    },
}


@router.get("/settings", response_model=dict)
async def get_all_settings(
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(AppSettings))
    settings = result.scalars().all()
    return {"data": [SettingResponse.model_validate(s) for s in settings]}


@router.put("/settings/{key}", response_model=dict)
async def update_setting(
    key: str,
    setting_in: SettingUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    existing = await db.get(AppSettings, key)
    if existing:
        existing.value = setting_in.value
    else:
        db.add(AppSettings(key=key, value=setting_in.value))
    await db.flush()
    setting = await db.get(AppSettings, key)
    await db.refresh(setting)
    return {"data": SettingResponse.model_validate(setting)}


@router.get("/settings/llm/providers", response_model=dict)
async def get_provider_presets() -> dict:
    return {"data": PROVIDER_PRESETS}


@router.post("/settings/llm/test", response_model=dict)
async def test_llm_connection(
    test_in: LLMTestRequest,
) -> dict:
    # TODO: Implement LLM connection test (Phase 2)
    return {"data": {"status": "not_implemented", "message": "LLM test coming in Phase 2"}}


@router.get("/settings/llm/ollama/models", response_model=dict)
async def list_ollama_models() -> dict:
    # TODO: Query Ollama API for local models (Phase 2)
    return {"data": []}

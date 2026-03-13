from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.garden import Garden
from verdanta.models.llm import LLMInteraction
from verdanta.schemas.advisor import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    InteractionResponse,
)

router = APIRouter()


@router.post("/gardens/{garden_id}/advisor/chat", response_model=dict)
async def chat(
    garden_id: int,
    chat_in: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Send a message to the garden advisor and receive an LLM-powered response."""
    from verdanta.services.advisor_service import AdvisorService

    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    svc = AdvisorService()
    try:
        response = await svc.chat(
            message=chat_in.message,
            garden=garden,
            db=db,
            planting_id=chat_in.planting_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Advisor unavailable: {exc}"
        ) from exc

    return {"data": ChatResponse.model_validate(response)}


@router.post("/gardens/{garden_id}/advisor/chat/stream")
async def chat_stream(
    garden_id: int,
    chat_in: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    # Streaming chat deferred to Phase 4 — use non-streaming /chat endpoint
    raise HTTPException(status_code=501, detail="Streaming not yet implemented; use /chat instead")


@router.get("/gardens/{garden_id}/advisor/alerts", response_model=dict)
async def get_alerts(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement proactive alerts (Phase 4)
    raise HTTPException(status_code=501, detail="Proactive alerts not yet implemented")


@router.post("/plantings/{planting_id}/advisor/diagnose", response_model=dict)
async def diagnose_photo(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # TODO: Implement photo diagnosis (Phase 4)
    raise HTTPException(status_code=501, detail="Photo diagnosis not yet implemented")


@router.get("/gardens/{garden_id}/advisor/history", response_model=dict)
async def interaction_history(
    garden_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(LLMInteraction)
        .where(LLMInteraction.garden_id == garden_id)
        .order_by(LLMInteraction.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    interactions = result.scalars().all()
    return {
        "data": [InteractionResponse.model_validate(i) for i in interactions],
        "count": len(interactions),
    }


@router.post("/advisor/interactions/{interaction_id}/feedback", response_model=dict)
async def submit_feedback(
    interaction_id: int,
    feedback_in: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    interaction = await db.get(LLMInteraction, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    interaction.feedback = feedback_in.feedback
    await db.flush()
    return {"data": {"status": "feedback_recorded"}}

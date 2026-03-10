from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.llm import LLMInteraction
from verdanta.schemas.advisor import (
    ChatRequest,
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
    # TODO: Implement LLM chat with context injection (Phase 4)
    raise HTTPException(status_code=501, detail="Advisor chat not yet implemented")


@router.post("/gardens/{garden_id}/advisor/chat/stream")
async def chat_stream(
    garden_id: int,
    chat_in: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    # TODO: Implement SSE streaming chat (Phase 4)
    raise HTTPException(status_code=501, detail="Streaming not yet implemented")


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

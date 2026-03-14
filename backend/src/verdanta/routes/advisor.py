import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.garden import Garden
from verdanta.models.llm import LLMInteraction
from verdanta.schemas.advisor import (
    ChatRequest,
    ChatResponse,
    DiagnosisRequest,
    FeedbackRequest,
    InteractionResponse,
)

logger = logging.getLogger(__name__)

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
) -> StreamingResponse:
    """Stream advisor response via SSE."""
    from datetime import UTC, datetime

    from verdanta.models.settings import AppSettings
    from verdanta.services.advisor_service import ADVISOR_SYSTEM_PROMPT, AdvisorService
    from verdanta.services.knowledge_service import write_knowledge_entry
    from verdanta.services.llm_service import create_llm_client, get_llm_config_from_settings

    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    # Assemble context before streaming
    svc = AdvisorService()
    context = await svc._assemble_context(garden, db, chat_in.planting_id)

    settings_result = await db.execute(select(AppSettings))
    db_settings = {s.key: s.value for s in settings_result.scalars().all()}
    config = await get_llm_config_from_settings(db_settings)
    client = create_llm_client(config)
    full_system = f"{ADVISOR_SYSTEM_PROMPT}\n\n{context}"

    async def event_generator():  # type: ignore[return]
        full_response = ""
        start = time.monotonic()
        try:
            async for chunk in client.stream(
                prompt=chat_in.message,
                system=full_system,
            ):
                full_response += chunk
                data = json.dumps({"chunk": chunk, "done": False})
                yield f"data: {data}\n\n"

            duration_ms = int((time.monotonic() - start) * 1000)

            # Log the interaction after streaming
            interaction = LLMInteraction(
                garden_id=garden.id,
                planting_id=chat_in.planting_id,
                interaction_type="advisor_chat",
                user_prompt=chat_in.message,
                system_context=context,
                response=full_response,
                model_used=config.model,
                provider=str(config.provider),
                status="completed",
                duration_ms=duration_ms,
                timestamp=datetime.now(UTC),
            )
            db.add(interaction)
            await db.flush()
            await db.refresh(interaction)

            # Write knowledge entry
            try:
                await write_knowledge_entry(
                    db=db,
                    source_type="advisor_conversation",
                    content=f"Q: {chat_in.message}\nA: {full_response}",
                    garden_id=garden.id,
                    source_id=interaction.id,
                    metadata={"planting_id": chat_in.planting_id},
                )
            except Exception:
                logger.warning("Failed to write knowledge entry", exc_info=True)

            await db.commit()

            done_data = json.dumps({
                "chunk": "",
                "done": True,
                "interaction_id": interaction.id,
            })
            yield f"data: {done_data}\n\n"

        except Exception as exc:
            logger.error("Streaming error: %s", exc, exc_info=True)
            error_data = json.dumps({
                "chunk": f"\n\n[Error: {exc}]",
                "done": True,
                "interaction_id": None,
            })
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )



@router.post("/plantings/{planting_id}/advisor/diagnose", response_model=dict)
async def diagnose_photo(
    planting_id: int,
    diagnosis_in: DiagnosisRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Analyze a photo of a plant using the LLM vision model."""
    from verdanta.models.planting import Photo, Planting
    from verdanta.services.advisor_service import AdvisorService

    planting = await db.get(Planting, planting_id)
    if not planting:
        raise HTTPException(status_code=404, detail="Planting not found")

    photo = await db.get(Photo, diagnosis_in.photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    garden = await db.get(Garden, planting.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    svc = AdvisorService()
    try:
        response = await svc.diagnose(
            planting=planting,
            photo=photo,
            garden=garden,
            db=db,
            question=diagnosis_in.question,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Diagnosis unavailable: {exc}"
        ) from exc

    return {"data": response}


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

"""Garden advisor service — LLM-powered chat with contextual garden awareness.

Assembles context from garden, active plantings, recent weather, and species
dossiers via the ContextProvider protocol. Logs every interaction and writes
knowledge entries.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.models.garden import Garden
from verdanta.models.llm import LLMInteraction
from verdanta.models.settings import AppSettings
from verdanta.schemas.advisor import ChatResponse
from verdanta.services.context_providers import ContextChunk, get_default_providers
from verdanta.services.knowledge_service import write_knowledge_entry
from verdanta.services.llm_service import create_llm_client, get_llm_config_from_settings

logger = logging.getLogger(__name__)

ADVISOR_SYSTEM_PROMPT = """\
You are Verdanta, an expert garden advisor with deep knowledge of horticulture, \
plant care, and local growing conditions. You have been given context about the \
user's garden, active plantings, and recent weather. Use this context to give \
specific, actionable advice tailored to their situation.

Guidelines:
- Be concise and practical — focus on what the gardener should actually do.
- Reference specific plants, weather conditions, or dates when relevant.
- If you are uncertain, say so rather than guessing.
- Suggest when to seek additional data (soil tests, pest identification, etc.).
- Keep responses conversational but informative.
"""


class AdvisorService:
    """Handles chat interactions with context assembly and LLM routing."""

    async def chat(
        self,
        message: str,
        garden: Garden,
        db: AsyncSession,
        planting_id: int | None = None,
    ) -> ChatResponse:
        """Assemble garden context, query the LLM, log the interaction."""
        context = await self._assemble_context(garden, db, planting_id)
        db_settings = await _load_settings(db)
        config = await get_llm_config_from_settings(db_settings)
        client = create_llm_client(config)

        full_system = f"{ADVISOR_SYSTEM_PROMPT}\n\n{context}"

        llm_response = await client.generate(
            prompt=message,
            system=full_system,
        )

        interaction = LLMInteraction(
            garden_id=garden.id,
            planting_id=planting_id,
            interaction_type="advisor_chat",
            user_prompt=message,
            system_context=context,
            response=llm_response.text,
            model_used=llm_response.model,
            provider=llm_response.provider,
            status="completed",
            duration_ms=llm_response.duration_ms,
            tokens_used=llm_response.tokens_used,
            timestamp=datetime.now(UTC),
        )
        db.add(interaction)
        await db.flush()
        await db.refresh(interaction)

        # Write knowledge entry for this Q&A pair
        try:
            await write_knowledge_entry(
                db=db,
                source_type="advisor_conversation",
                content=f"Q: {message}\nA: {llm_response.text}",
                garden_id=garden.id,
                source_id=interaction.id,
                metadata={
                    "planting_id": planting_id,
                    "model": llm_response.model,
                },
            )
        except Exception:
            logger.warning("Failed to write knowledge entry for advisor chat", exc_info=True)

        return ChatResponse(
            response=llm_response.text,
            model_used=llm_response.model,
            provider=llm_response.provider,
            context_summary=_summarize_context(garden, context),
            interaction_id=interaction.id,
        )

    async def _assemble_context(
        self,
        garden: Garden,
        db: AsyncSession,
        planting_id: int | None = None,
    ) -> str:
        """Build a text context block using registered ContextProviders."""
        parts: list[str] = []

        # Garden overview (always included)
        parts.append(
            f"## Garden: {garden.name}\n"
            f"- Location: {garden.latitude:.4f}°, {garden.longitude:.4f}°\n"
            f"- Timezone: {garden.timezone}\n"
            f"- USDA Zone: {garden.usda_zone or 'unknown'}\n"
            f"- Soil type: {garden.soil_type_default or 'unknown'}\n"
        )

        # Collect context from all providers
        providers = get_default_providers()
        all_chunks: list[ContextChunk] = []
        for provider in providers:
            try:
                chunks = await provider.get_context(
                    garden_id=garden.id,
                    db=db,
                    planting_id=planting_id,
                )
                all_chunks.extend(chunks)
            except Exception:
                logger.warning(
                    "Context provider %s failed",
                    provider.provider_name,
                    exc_info=True,
                )

        # Sort by relevance (highest first) and assemble
        all_chunks.sort(key=lambda c: c.relevance, reverse=True)
        for chunk in all_chunks:
            parts.append(chunk.content)

        parts.append(f"\n## Today's Date\n{datetime.now(UTC).date()}")
        return "\n".join(parts)


async def _load_settings(db: AsyncSession) -> dict[str, str]:
    result = await db.execute(select(AppSettings))
    return {s.key: s.value for s in result.scalars().all()}


def _summarize_context(garden: Garden, context: str) -> str:
    """Return a brief description of what context was assembled."""
    lines = context.strip().split("\n")
    return f"Garden '{garden.name}' — {len(lines)} context lines assembled"

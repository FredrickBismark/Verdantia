"""Knowledge entry write pipeline.

Stores text chunks in the knowledge_entries table as a side effect
of other operations. Does NOT build embeddings yet.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.models.knowledge import KnowledgeEntry

logger = logging.getLogger(__name__)


async def write_knowledge_entry(
    db: AsyncSession,
    source_type: str,
    content: str,
    garden_id: int | None = None,
    source_id: int | None = None,
    metadata: dict | None = None,
    chunk_index: int = 0,
) -> KnowledgeEntry:
    """Write a knowledge entry to the database."""
    entry = KnowledgeEntry(
        garden_id=garden_id,
        source_type=source_type,
        source_id=source_id,
        content=content[:10000],
        metadata_json=metadata,
        chunk_index=chunk_index,
    )
    db.add(entry)
    await db.flush()
    return entry

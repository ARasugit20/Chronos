import asyncio

import structlog
from celery import shared_task

from app.adapters.macro_source import MacroMockSource
from app.adapters.news_source import NewsMockSource
from app.adapters.sports_source import SportsMockSource
from app.database import SessionLocal
from app.redis_client import get_redis
from app.services.pipeline_service import ingest_event

logger = structlog.get_logger(__name__)


async def _run_all_sources() -> int:
    sources = [SportsMockSource(), MacroMockSource(), NewsMockSource()]
    processed = 0
    redis_client = get_redis()
    async with SessionLocal() as db:
        for source in sources:
            events = await source.fetch()
            for raw in events:
                _, _, duplicate = await ingest_event(
                    db=db,
                    redis_client=redis_client,
                    source=raw["source"],
                    event_type=raw["event_type"],
                    title=raw["title"],
                    occurred_at=raw["occurred_at"],
                    metadata=raw["metadata"],
                )
                if not duplicate:
                    processed += 1
    logger.info("ingest.completed", processed=processed)
    return processed


@shared_task(name="app.workers.ingest_tasks.run_all_sources")
def run_all_sources() -> int:
    return asyncio.run(_run_all_sources())

import asyncio

import structlog
from celery import shared_task
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.outcome import Outcome

logger = structlog.get_logger(__name__)


async def run_retrain() -> int:
    async with SessionLocal() as db:
        count = (await db.execute(select(func.count()).select_from(Outcome))).scalar_one()
    logger.info("retrain triggered", n=count)
    return int(count)


@shared_task(name="app.workers.retrain_task.run_retrain")
def run_retrain_task() -> int:
    return asyncio.run(run_retrain())

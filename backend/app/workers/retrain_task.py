import asyncio

import structlog
from celery import shared_task
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.outcome import Outcome

logger = structlog.get_logger(__name__)


async def run_retrain() -> int:
    from app.pipeline.train_stub import run_model_retrain

    trained = await run_model_retrain()
    async with SessionLocal() as db:
        outcomes = (await db.execute(select(Outcome).limit(200))).scalars().all()
    if len(outcomes) >= 5:
        raw = [o.recommendation.signal.probability_raw for o in outcomes if o.recommendation and o.recommendation.signal]
        hits = [int(o.hit_boolean) for o in outcomes]
        if len(raw) == len(hits) and raw:
            from app.pipeline.calibrator import IsotonicCalibrator

            cal = IsotonicCalibrator()
            cal.fit(raw, hits)
    logger.info("retrain triggered", n=trained)
    return int(trained)


@shared_task(name="app.workers.retrain_task.run_retrain")
def run_retrain_task() -> int:
    return asyncio.run(run_retrain())

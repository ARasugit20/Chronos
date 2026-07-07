import asyncio

import structlog
from celery import shared_task

logger = structlog.get_logger(__name__)


async def run_retrain() -> int:
    from app.pipeline.train_stub import run_model_retrain

    report = await run_model_retrain()
    logger.info("retrain.triggered", **report.__dict__)
    return report.train_samples


@shared_task(name="app.workers.retrain_task.run_retrain")
def run_retrain_task() -> int:
    return asyncio.run(run_retrain())

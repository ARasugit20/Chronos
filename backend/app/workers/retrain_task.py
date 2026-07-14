import asyncio

import structlog
from celery import shared_task

from app.config import get_settings
from app.database import SessionLocal
from app.models.model_run import ModelRun

logger = structlog.get_logger(__name__)


async def run_retrain() -> int:
    from app.pipeline.train_stub import run_model_retrain

    report = await run_model_retrain()
    settings = get_settings()
    async with SessionLocal() as db:
        db.add(
            ModelRun(
                model_version="lgbm-v1",
                status="candidate" if report.oos_brier is not None else "insufficient_data",
                dataset_start_at=report.dataset_start_at,
                dataset_cutoff_at=report.dataset_cutoff_at,
                feature_schema_hash=report.feature_schema_hash,
                artifact_path=settings.model_path or "models/lgbm_scorer.pkl",
                train_samples=report.train_samples,
                calibrate_samples=report.calibrate_samples,
                test_samples=report.test_samples,
                train_brier=report.train_brier,
                oos_brier=report.oos_brier,
                oos_hit_rate=report.oos_hit_rate,
                parameters_json={
                    "n_estimators": 100,
                    "learning_rate": 0.05,
                    "num_leaves": 31,
                },
            )
        )
        await db.commit()
    logger.info("retrain.triggered", **report.__dict__)
    return report.train_samples


@shared_task(name="app.workers.retrain_task.run_retrain")
def run_retrain_task() -> int:
    return asyncio.run(run_retrain())

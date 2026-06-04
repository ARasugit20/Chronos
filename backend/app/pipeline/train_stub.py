# WHY: Weekly retrain hook fitting LightGBM from historical outcomes.

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import SessionLocal
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.pipeline.features import extract_features, features_to_vector
from app.pipeline.scorer import LightGBMScorer

logger = structlog.get_logger(__name__)


async def run_model_retrain() -> int:
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(Outcome)
                .options(
                    selectinload(Outcome.recommendation).selectinload(Recommendation.signal),
                )
                .limit(500)
            )
        ).scalars().all()

    if len(rows) < 10:
        logger.info("retrain.skipped", reason="insufficient_outcomes", count=len(rows))
        return len(rows)

    X: list[list[float]] = []
    y: list[int] = []
    for outcome in rows:
        rec = outcome.recommendation
        if rec is None or rec.signal is None or rec.signal.event is None:
            continue
        event = rec.signal.event
        features = extract_features(event)
        X.append(features_to_vector(features))
        y.append(1 if outcome.hit_boolean else 0)

    if len(X) < 10:
        return len(X)

    brier = LightGBMScorer.train(X, y)
    logger.info("retrain.completed", samples=len(X), brier=brier)
    return len(X)

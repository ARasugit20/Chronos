# WHY: Weekly retrain hook fitting LightGBM from historical outcomes with temporal validation.

from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import SessionLocal
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.models.signal import Signal
from app.pipeline.calibrator import IsotonicCalibrator
from app.pipeline.features import extract_features, features_to_vector
from app.pipeline.scorer import LightGBMScorer
from app.pipeline.temporal_split import split_by_time

logger = structlog.get_logger(__name__)


@dataclass
class RetrainReport:
    train_samples: int
    calibrate_samples: int
    test_samples: int
    train_brier: float | None
    oos_hit_rate: float | None
    oos_brier: float | None


def _outcome_rows(rows: list[Outcome]) -> tuple[list[list[float]], list[int], list[float], list[int]]:
    x_rows: list[list[float]] = []
    y_rows: list[int] = []
    raw_probs: list[float] = []
    hits: list[int] = []
    for outcome in rows:
        rec = outcome.recommendation
        if rec is None or rec.signal is None or rec.signal.event is None:
            continue
        event = rec.signal.event
        features = extract_features(event, None)
        x_rows.append(features_to_vector(features))
        y_rows.append(1 if outcome.hit_boolean else 0)
        raw_probs.append(rec.signal.probability_raw)
        hits.append(1 if outcome.hit_boolean else 0)
    return x_rows, y_rows, raw_probs, hits


async def run_model_retrain() -> RetrainReport:
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(Outcome)
                .options(
                    selectinload(Outcome.recommendation)
                    .selectinload(Recommendation.signal)
                    .selectinload(Signal.event),
                )
                .order_by(Outcome.resolved_at.asc())
                .limit(500)
            )
        ).scalars().all()

    if len(rows) < 10:
        logger.info("retrain.skipped", reason="insufficient_outcomes", count=len(rows))
        return RetrainReport(
            train_samples=len(rows),
            calibrate_samples=0,
            test_samples=0,
            train_brier=None,
            oos_hit_rate=None,
            oos_brier=None,
        )

    split = split_by_time(list(rows), sort_key=lambda row: row.resolved_at)
    train_x, train_y, _, _ = _outcome_rows(split.train)
    _, _, calibrate_raw, calibrate_hits = _outcome_rows(split.calibrate)
    _, _, test_raw, test_hits = _outcome_rows(split.test)

    train_brier: float | None = None
    if len(train_x) >= 10:
        train_brier = LightGBMScorer.train(train_x, train_y)

    if len(calibrate_raw) >= 5:
        calibrator = IsotonicCalibrator()
        calibrator.fit(calibrate_raw, calibrate_hits)

    oos_hit_rate: float | None = None
    oos_brier: float | None = None
    if test_raw and test_hits:
        calibrator = IsotonicCalibrator()
        calibrated = [calibrator.calibrate(raw) for raw in test_raw]
        oos_hit_rate = sum(test_hits) / len(test_hits)
        oos_brier = sum((p - float(h)) ** 2 for p, h in zip(calibrated, test_hits, strict=True)) / len(test_hits)

    report = RetrainReport(
        train_samples=len(train_x),
        calibrate_samples=len(calibrate_raw),
        test_samples=len(test_raw),
        train_brier=train_brier,
        oos_hit_rate=oos_hit_rate,
        oos_brier=oos_brier,
    )
    logger.info("retrain.completed", **report.__dict__)
    return report

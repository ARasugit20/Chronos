# WHY: Summarize resolved recommendation outcomes for model-quality monitoring.

from __future__ import annotations

from dataclasses import dataclass

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.models.signal import Signal


@dataclass
class OutcomeMetricsResult:
    methodology: str
    total_resolved: int
    hit_rate: float
    mean_brier: float
    precision_by_ticker: dict[str, float]
    bucket_reliability: dict[str, dict[str, float]]
    ml_ready: bool
    paper_trading: bool
    note: str


def _bucket_reliability(rows: Sequence[Outcome]) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[tuple[float, int]]] = {}
    for row in rows:
        rec = row.recommendation
        if rec is None or rec.signal is None:
            continue
        bucket = rec.signal.confidence_bucket
        buckets.setdefault(bucket, []).append(
            (rec.signal.probability_calibrated, 1 if row.hit_boolean else 0)
        )

    reliability: dict[str, dict[str, float]] = {}
    for bucket, values in buckets.items():
        if not values:
            continue
        predicted = sum(prob for prob, _ in values) / len(values)
        observed = sum(hit for _, hit in values) / len(values)
        reliability[bucket] = {
            "samples": float(len(values)),
            "mean_predicted": predicted,
            "observed_hit_rate": observed,
            "calibration_gap": abs(predicted - observed),
        }
    return reliability


async def run_outcome_metrics(db: AsyncSession, *, ml_min_outcomes: int = 50) -> OutcomeMetricsResult:
    rows = (
        await db.execute(
            select(Outcome)
            .options(
                selectinload(Outcome.recommendation).selectinload(Recommendation.signal),
            )
            .order_by(Outcome.resolved_at.desc())
            .limit(500)
        )
    ).scalars().all()

    if not rows:
        return OutcomeMetricsResult(
            methodology="resolved_outcome_metrics",
            total_resolved=0,
            hit_rate=0.0,
            mean_brier=0.0,
            precision_by_ticker={},
            bucket_reliability={},
            ml_ready=False,
            paper_trading=True,
            note="Reports realized outcomes only; not a point-in-time historical replay.",
        )

    hits = [1 if row.hit_boolean else 0 for row in rows]
    briers = [float(row.brier_component) for row in rows]
    ticker_hits: dict[str, list[int]] = {}

    for row in rows:
        rec = row.recommendation
        if rec is None or rec.signal is None:
            continue
        ticker = rec.signal.ticker
        ticker_hits.setdefault(ticker, []).append(1 if row.hit_boolean else 0)

    precision = {
        ticker: sum(vals) / len(vals)
        for ticker, vals in ticker_hits.items()
        if len(vals) >= 3
    }

    return OutcomeMetricsResult(
        methodology="resolved_outcome_metrics",
        total_resolved=len(rows),
        hit_rate=sum(hits) / len(hits),
        mean_brier=sum(briers) / len(briers),
        precision_by_ticker=precision,
        bucket_reliability=_bucket_reliability(rows),
        ml_ready=len(rows) >= ml_min_outcomes,
        paper_trading=True,
        note="Reports realized outcomes only; not a point-in-time historical replay.",
    )


# Backward-compatible alias used by existing imports/tests.
async def run_backtest(db: AsyncSession, *, ml_min_outcomes: int = 50) -> OutcomeMetricsResult:
    return await run_outcome_metrics(db, ml_min_outcomes=ml_min_outcomes)


async def evaluate_signal_quality(db: AsyncSession, ticker: str, lookback: int = 30) -> dict[str, float]:
    rows = (
        await db.execute(
            select(Outcome)
            .join(Recommendation, Outcome.recommendation_id == Recommendation.id)
            .join(Signal, Recommendation.signal_id == Signal.id)
            .where(Signal.ticker == ticker)
            .order_by(Outcome.resolved_at.desc())
            .limit(lookback)
        )
    ).scalars().all()

    if not rows:
        return {"precision": 0.0, "samples": 0.0, "mean_return_pct": 0.0}

    hits = [1 if row.hit_boolean else 0 for row in rows]
    returns = [float(row.realized_return_pct) for row in rows]
    return {
        "precision": sum(hits) / len(hits),
        "samples": float(len(rows)),
        "mean_return_pct": sum(returns) / len(returns),
    }

# WHY: Summarize resolved recommendation outcomes for model-quality monitoring.

from __future__ import annotations

from dataclasses import dataclass

from collections.abc import Sequence
import math

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
    mean_return_pct: float
    return_volatility: float
    max_drawdown_pct: float
    calibration_error: float
    hit_rate_ci95: tuple[float, float]
    rolling_30: dict[str, float]
    ml_ready: bool
    paper_trading: bool
    note: str


def wilson_interval(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return (0.0, 0.0)
    proportion = hits / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2))
        / denominator
    )
    return (max(0.0, center - margin), min(1.0, center + margin))


def maximum_drawdown(returns: Sequence[float]) -> float:
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in returns:
        equity *= 1 + value
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, (peak - equity) / peak)
    return max_drawdown


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
            mean_return_pct=0.0,
            return_volatility=0.0,
            max_drawdown_pct=0.0,
            calibration_error=0.0,
            hit_rate_ci95=(0.0, 0.0),
            rolling_30={"samples": 0.0, "hit_rate": 0.0, "mean_brier": 0.0},
            ml_ready=False,
            paper_trading=True,
            note="Reports realized outcomes only; not a point-in-time historical replay.",
        )

    hits = [1 if row.hit_boolean else 0 for row in rows]
    briers = [float(row.brier_component) for row in rows]
    returns = [float(row.realized_return_pct) for row in rows]
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
    mean_return = sum(returns) / len(returns)
    variance = sum((value - mean_return) ** 2 for value in returns) / len(returns)
    reliability = _bucket_reliability(rows)
    calibration_error = (
        sum(values["calibration_gap"] * values["samples"] for values in reliability.values())
        / len(rows)
        if rows
        else 0.0
    )
    recent_hits = hits[:30]
    recent_briers = briers[:30]

    return OutcomeMetricsResult(
        methodology="resolved_outcome_metrics",
        total_resolved=len(rows),
        hit_rate=sum(hits) / len(hits),
        mean_brier=sum(briers) / len(briers),
        precision_by_ticker=precision,
        bucket_reliability=reliability,
        mean_return_pct=mean_return,
        return_volatility=math.sqrt(variance),
        max_drawdown_pct=maximum_drawdown(list(reversed(returns))),
        calibration_error=calibration_error,
        hit_rate_ci95=wilson_interval(sum(hits), len(hits)),
        rolling_30={
            "samples": float(len(recent_hits)),
            "hit_rate": sum(recent_hits) / len(recent_hits),
            "mean_brier": sum(recent_briers) / len(recent_briers),
        },
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

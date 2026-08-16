# WHY: Summarize resolved recommendation outcomes for model-quality monitoring.

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.models.signal import Signal
from app.pipeline.sectors import ticker_sector


@dataclass
class BreakdownStats:
    samples: int = 0
    hit_rate: float = 0.0
    mean_brier: float = 0.0
    expectancy: float = 0.0
    profit_factor: float = 0.0


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
    expectancy: float = 0.0
    profit_factor: float = 0.0
    mean_win_pct: float = 0.0
    mean_loss_pct: float = 0.0
    by_confidence_bucket: dict[str, BreakdownStats] = field(default_factory=dict)
    by_theme_bucket: dict[str, BreakdownStats] = field(default_factory=dict)
    by_regime: dict[str, BreakdownStats] = field(default_factory=dict)
    sector_contribution: dict[str, float] = field(default_factory=dict)


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


def _profit_metrics(returns: Sequence[float], hits: Sequence[int]) -> tuple[float, float, float, float]:
    if not returns:
        return (0.0, 0.0, 0.0, 0.0)
    expectancy = sum(returns) / len(returns)
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r < 0]
    mean_win = sum(wins) / len(wins) if wins else 0.0
    mean_loss = sum(losses) / len(losses) if losses else 0.0
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else (gross_win if gross_win > 0 else 0.0)
    _ = hits
    return expectancy, profit_factor, mean_win, mean_loss


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


def _breakdown(rows: Sequence[Outcome], key_fn) -> dict[str, BreakdownStats]:
    grouped: dict[str, list[Outcome]] = {}
    for row in rows:
        rec = row.recommendation
        if rec is None:
            continue
        key = key_fn(rec)
        if key is None:
            continue
        grouped.setdefault(key, []).append(row)

    result: dict[str, BreakdownStats] = {}
    for key, group in grouped.items():
        returns = [float(r.realized_return_pct) for r in group]
        hits = [1 if r.hit_boolean else 0 for r in group]
        briers = [float(r.brier_component) for r in group]
        exp, pf, _, _ = _profit_metrics(returns, hits)
        result[key] = BreakdownStats(
            samples=len(group),
            hit_rate=sum(hits) / len(hits),
            mean_brier=sum(briers) / len(briers),
            expectancy=exp,
            profit_factor=pf,
        )
    return result


def _sector_contribution(rows: Sequence[Outcome]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for row in rows:
        rec = row.recommendation
        if rec is None or rec.signal is None:
            continue
        sector = ticker_sector(rec.signal.ticker)
        totals[sector] = totals.get(sector, 0.0) + float(row.realized_return_pct)
    return totals


async def run_outcome_metrics(db: AsyncSession, *, ml_min_outcomes: int = 50) -> OutcomeMetricsResult:
    settings = get_settings()
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

    note = "Reports realized outcomes only; not a point-in-time historical replay."

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
            paper_trading=settings.paper_trading_mode,
            note=note,
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
    expectancy, profit_factor, mean_win, mean_loss = _profit_metrics(returns, hits)

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
        paper_trading=settings.paper_trading_mode,
        note=note,
        expectancy=expectancy,
        profit_factor=profit_factor,
        mean_win_pct=mean_win,
        mean_loss_pct=mean_loss,
        by_confidence_bucket=_breakdown(rows, lambda rec: rec.signal.confidence_bucket if rec.signal else None),
        by_theme_bucket=_breakdown(rows, lambda rec: rec.theme_bucket),
        by_regime=_breakdown(rows, lambda rec: rec.regime),
        sector_contribution=_sector_contribution(rows),
    )


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

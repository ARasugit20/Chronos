# WHY: Backtest recommendation quality against resolved outcomes.

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.models.signal import Signal


@dataclass
class BacktestResult:
    total_resolved: int
    hit_rate: float
    mean_brier: float
    precision_by_ticker: dict[str, float]
    ml_ready: bool
    paper_trading: bool


async def run_backtest(db: AsyncSession, *, ml_min_outcomes: int = 50) -> BacktestResult:
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
        return BacktestResult(
            total_resolved=0,
            hit_rate=0.0,
            mean_brier=0.0,
            precision_by_ticker={},
            ml_ready=False,
            paper_trading=True,
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

    return BacktestResult(
        total_resolved=len(rows),
        hit_rate=sum(hits) / len(hits),
        mean_brier=sum(briers) / len(briers),
        precision_by_ticker=precision,
        ml_ready=len(rows) >= ml_min_outcomes,
        paper_trading=True,
    )


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

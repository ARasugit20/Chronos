# WHY: Expose portfolio cash, deployment, and cap utilization for risk dashboard.

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.recommendation import Recommendation
from app.models.signal import Signal
from app.pipeline.allocator import MAX_TICKER_PCT
from app.pipeline.sectors import ticker_sector

ACTIVE_STATUSES = {"pending", "approved"}


@dataclass
class TickerExposureRow:
    ticker: str
    sector: str
    amount_usd: float
    pct_portfolio: float
    pct_ticker_cap: float


@dataclass
class PortfolioSnapshot:
    portfolio_cash: float
    portfolio_value: float
    available_cash: float
    total_deployed: float
    pct_deployed: float
    sector_cap_pct: float
    max_ticker_pct: float
    open_recommendations: int
    ticker_exposure: list[TickerExposureRow]
    sector_exposure: dict[str, float]


async def get_portfolio_snapshot(db: AsyncSession) -> PortfolioSnapshot:
    settings = get_settings()
    rows = (
        await db.execute(
            select(Recommendation, Signal)
            .join(Signal, Recommendation.signal_id == Signal.id)
            .options(selectinload(Recommendation.signal))
            .where(
                Recommendation.status.in_(ACTIVE_STATUSES),
                Recommendation.action.in_(("buy", "paper_buy")),
            )
        )
    ).all()

    ticker_amounts: dict[str, float] = {}
    sector_amounts: dict[str, float] = {}
    for rec, signal in rows:
        amount = float(rec.amount_usd)
        ticker_amounts[signal.ticker] = ticker_amounts.get(signal.ticker, 0.0) + amount
        sector = ticker_sector(signal.ticker)
        sector_amounts[sector] = sector_amounts.get(sector, 0.0) + amount

    total_deployed = sum(ticker_amounts.values())
    available_cash = max(0.0, settings.portfolio_cash - total_deployed)
    pct_deployed = total_deployed / settings.portfolio_value if settings.portfolio_value > 0 else 0.0

    ticker_exposure = [
        TickerExposureRow(
            ticker=ticker,
            sector=ticker_sector(ticker),
            amount_usd=round(amount, 2),
            pct_portfolio=round(amount / settings.portfolio_value, 4) if settings.portfolio_value else 0.0,
            pct_ticker_cap=round(amount / (settings.portfolio_value * MAX_TICKER_PCT), 4)
            if settings.portfolio_value
            else 0.0,
        )
        for ticker, amount in sorted(ticker_amounts.items(), key=lambda item: item[1], reverse=True)
    ]

    sector_exposure = {
        sector: round(amount / settings.portfolio_value, 4) if settings.portfolio_value else 0.0
        for sector, amount in sorted(sector_amounts.items(), key=lambda item: item[1], reverse=True)
    }

    return PortfolioSnapshot(
        portfolio_cash=settings.portfolio_cash,
        portfolio_value=settings.portfolio_value,
        available_cash=round(available_cash, 2),
        total_deployed=round(total_deployed, 2),
        pct_deployed=round(pct_deployed, 4),
        sector_cap_pct=settings.sector_cap_pct,
        max_ticker_pct=MAX_TICKER_PCT,
        open_recommendations=len(rows),
        ticker_exposure=ticker_exposure,
        sector_exposure=sector_exposure,
    )

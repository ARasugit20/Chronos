# WHY: Half-Kelly position sizing with sector heat and drawdown guards.

from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings

MAX_TICKER_PCT = 0.08
KELLY_FRACTION = 0.5


@dataclass
class AllocationResult:
    amount_usd: float
    pct_cash: float
    kelly_full_pct: float
    kelly_half_pct: float
    adjustment_reason: str | None = None


def compute_allocation(
    probability: float,
    available_cash: float,
    existing_positions: dict[str, float],
    portfolio_value: float,
    ticker: str,
    sector: str,
    *,
    recent_hits: list[bool] | None = None,
    sector_pending_usd: float = 0.0,
) -> AllocationResult:
    settings = get_settings()
    odds = settings.kelly_odds
    sector_cap = settings.sector_cap_pct
    min_usd = settings.min_allocation_usd

    kelly_full = (odds * probability - (1 - probability)) / odds
    kelly_half = kelly_full * KELLY_FRACTION
    raw_amount = kelly_half * available_cash
    adjustment_reason = None

    ticker_exposure = existing_positions.get(ticker, 0.0)
    max_ticker_amount = portfolio_value * MAX_TICKER_PCT - ticker_exposure
    amount = min(raw_amount, max_ticker_amount)

    from app.pipeline.sectors import ticker_sector

    sector_exposure = sum(
        value for key, value in existing_positions.items() if ticker_sector(key) == sector
    )
    sector_total = sector_exposure + sector_pending_usd
    if sector_total > portfolio_value * sector_cap:
        amount *= 0.5
        adjustment_reason = "sector_heat_guard"

    if recent_hits and len(recent_hits) >= 5 and sum(1 for h in recent_hits[-5:] if not h) >= 3:
        amount *= 0.7
        adjustment_reason = "drawdown_guard"

    if kelly_full < 0 or amount < min_usd:
        return AllocationResult(0.0, 0.0, kelly_full, kelly_half, "below_kelly_threshold")

    amount = round(amount, 2)
    pct_cash = amount / available_cash if available_cash > 0 else 0.0
    return AllocationResult(amount, pct_cash, kelly_full, kelly_half, adjustment_reason)

# WHY: Half-Kelly position sizing with sector heat, drawdown, and regime delever guards.

from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.pipeline.regime import Regime, RegimeSnapshot

MAX_TICKER_PCT = 0.08
KELLY_FRACTION = 0.5


@dataclass
class AllocationResult:
    amount_usd: float
    pct_cash: float
    kelly_full_pct: float
    kelly_half_pct: float
    adjustment_reason: str | None = None


def _compose_reason(*parts: str | None) -> str | None:
    filtered = [part for part in parts if part]
    return "; ".join(filtered) if filtered else None


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
    regime: RegimeSnapshot | None = None,
    odds_override: float | None = None,
) -> AllocationResult:
    settings = get_settings()
    odds = odds_override if odds_override is not None else settings.kelly_odds
    sector_cap = settings.sector_cap_pct
    min_usd = settings.min_allocation_usd

    kelly_fraction = KELLY_FRACTION
    reasons: list[str] = []
    if regime is not None:
        if regime.kelly_fraction_override is not None:
            kelly_fraction = regime.kelly_fraction_override
            reasons.append(f"regime_kelly={kelly_fraction:.2f}")
        if regime.primary in {
            Regime.RISK_OFF_GEO,
            Regime.AI_INFRA_STRESS,
            Regime.EARNINGS_SELLTHEBEAT,
        }:
            kelly_fraction = min(kelly_fraction, regime.kelly_fraction_override or (1 / 3))
            reasons.append(f"regime_delever={regime.primary.value}")
        if "august_seasonality" in regime.flags:
            kelly_fraction *= 0.85
            reasons.append("august_seasonality_delever")

    kelly_full = (odds * probability - (1 - probability)) / odds
    kelly_half = kelly_full * kelly_fraction
    raw_amount = kelly_half * available_cash
    adjustment_reason: str | None = None

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
        adjustment_reason = _compose_reason(adjustment_reason, "sector_heat_guard")

    if recent_hits and len(recent_hits) >= 5 and sum(1 for h in recent_hits[-5:] if not h) >= 3:
        amount *= 0.7
        adjustment_reason = _compose_reason(adjustment_reason, "drawdown_guard")

    if kelly_full < 0 or amount < min_usd:
        return AllocationResult(
            0.0,
            0.0,
            kelly_full,
            kelly_half,
            _compose_reason("below_kelly_threshold", *reasons),
        )

    amount = round(amount, 2)
    pct_cash = amount / available_cash if available_cash > 0 else 0.0
    return AllocationResult(
        amount,
        pct_cash,
        kelly_full,
        kelly_half,
        _compose_reason(adjustment_reason, *reasons),
    )

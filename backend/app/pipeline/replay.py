"""Point-in-time historical replay primitives.

The replay engine consumes observations assembled with information available at
the signal timestamp. It never queries current application state or future
features, which keeps evaluation reproducible and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReplayAssumptions:
    initial_cash: float = 100_000.0
    allocation_pct: float = 0.02
    commission_bps: float = 1.0
    slippage_bps: float = 5.0


@dataclass(frozen=True)
class ReplayObservation:
    ticker: str
    signal_at: datetime
    expires_at: datetime
    entry_price: float
    exit_price: float
    probability: float
    benchmark_return_pct: float = 0.0


@dataclass(frozen=True)
class ReplayTrade:
    ticker: str
    signal_at: datetime
    expires_at: datetime
    gross_return_pct: float
    net_return_pct: float
    benchmark_return_pct: float
    alpha_pct: float
    pnl_usd: float


@dataclass(frozen=True)
class ReplayResult:
    methodology: str
    assumptions: ReplayAssumptions
    trades: list[ReplayTrade]
    ending_cash: float
    total_return_pct: float
    benchmark_return_pct: float
    alpha_pct: float
    hit_rate: float
    max_drawdown_pct: float


def _validate(observation: ReplayObservation) -> None:
    if observation.signal_at >= observation.expires_at:
        raise ValueError("signal_at must precede expires_at")
    if observation.entry_price <= 0 or observation.exit_price <= 0:
        raise ValueError("prices must be positive")
    if not 0.0 <= observation.probability <= 1.0:
        raise ValueError("probability must be between 0 and 1")


def run_historical_replay(
    observations: list[ReplayObservation],
    assumptions: ReplayAssumptions | None = None,
) -> ReplayResult:
    assumptions = assumptions or ReplayAssumptions()
    if assumptions.initial_cash <= 0:
        raise ValueError("initial_cash must be positive")
    if not 0 < assumptions.allocation_pct <= 1:
        raise ValueError("allocation_pct must be in (0, 1]")

    ordered = sorted(observations, key=lambda row: (row.signal_at, row.ticker))
    cash = assumptions.initial_cash
    peak = cash
    max_drawdown = 0.0
    benchmark_curve = assumptions.initial_cash
    trades: list[ReplayTrade] = []
    cost_pct = (assumptions.commission_bps + assumptions.slippage_bps) / 10_000

    for observation in ordered:
        _validate(observation)
        notional = cash * assumptions.allocation_pct
        gross_return = observation.exit_price / observation.entry_price - 1
        net_return = gross_return - cost_pct
        pnl = notional * net_return
        cash += pnl
        benchmark_curve *= 1 + assumptions.allocation_pct * observation.benchmark_return_pct
        peak = max(peak, cash)
        drawdown = (peak - cash) / peak if peak else 0.0
        max_drawdown = max(max_drawdown, drawdown)
        trades.append(
            ReplayTrade(
                ticker=observation.ticker,
                signal_at=observation.signal_at,
                expires_at=observation.expires_at,
                gross_return_pct=gross_return,
                net_return_pct=net_return,
                benchmark_return_pct=observation.benchmark_return_pct,
                alpha_pct=net_return - observation.benchmark_return_pct,
                pnl_usd=pnl,
            )
        )

    total_return = cash / assumptions.initial_cash - 1
    benchmark_return = benchmark_curve / assumptions.initial_cash - 1
    hit_rate = sum(trade.net_return_pct > 0 for trade in trades) / len(trades) if trades else 0.0
    return ReplayResult(
        methodology="point_in_time_replay",
        assumptions=assumptions,
        trades=trades,
        ending_cash=cash,
        total_return_pct=total_return,
        benchmark_return_pct=benchmark_return,
        alpha_pct=total_return - benchmark_return,
        hit_rate=hit_rate,
        max_drawdown_pct=max_drawdown,
    )

from datetime import datetime, timedelta, timezone

import pytest

from app.pipeline.replay import ReplayAssumptions, ReplayObservation, run_historical_replay


def observation(
    *,
    ticker: str = "AAPL",
    entry: float = 100.0,
    exit_price: float = 110.0,
    benchmark: float = 0.02,
) -> ReplayObservation:
    signal_at = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    return ReplayObservation(
        ticker=ticker,
        signal_at=signal_at,
        expires_at=signal_at + timedelta(days=3),
        entry_price=entry,
        exit_price=exit_price,
        probability=0.62,
        benchmark_return_pct=benchmark,
    )


def test_replay_applies_costs_and_reports_alpha() -> None:
    result = run_historical_replay(
        [observation()],
        ReplayAssumptions(
            initial_cash=10_000,
            allocation_pct=0.10,
            commission_bps=1,
            slippage_bps=4,
        ),
    )

    assert result.methodology == "point_in_time_replay"
    assert result.trades[0].gross_return_pct == pytest.approx(0.10)
    assert result.trades[0].net_return_pct == pytest.approx(0.0995)
    assert result.ending_cash == pytest.approx(10_099.50)
    assert result.alpha_pct < result.total_return_pct


def test_replay_is_deterministic_regardless_of_input_order() -> None:
    first = observation(ticker="AAPL")
    second = observation(ticker="MSFT", entry=200, exit_price=180, benchmark=-0.01)
    assert run_historical_replay([first, second]) == run_historical_replay([second, first])


def test_replay_rejects_non_point_in_time_window() -> None:
    row = observation()
    invalid = ReplayObservation(
        ticker=row.ticker,
        signal_at=row.expires_at,
        expires_at=row.signal_at,
        entry_price=row.entry_price,
        exit_price=row.exit_price,
        probability=row.probability,
    )
    with pytest.raises(ValueError, match="signal_at"):
        run_historical_replay([invalid])

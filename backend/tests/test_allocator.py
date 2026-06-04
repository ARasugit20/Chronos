from app.pipeline import allocator


def test_allocation_within_bounds() -> None:
    result = allocator.compute_allocation(
        probability=0.65,
        available_cash=10_000.0,
        existing_positions={},
        portfolio_value=50_000.0,
        ticker="NKE",
        sector="consumer",
    )
    assert 100 <= result.amount_usd <= 800
    assert result.pct_cash < 0.08


def test_low_probability_skips() -> None:
    result = allocator.compute_allocation(
        probability=0.35,
        available_cash=10_000.0,
        existing_positions={},
        portfolio_value=50_000.0,
        ticker="NKE",
        sector="consumer",
    )
    assert result.amount_usd == 0.0
    assert result.pct_cash == 0.0


def test_ticker_cap_enforced() -> None:
    existing = {"NKE": 0.079 * 50_000.0}
    result = allocator.compute_allocation(
        probability=0.65,
        available_cash=10_000.0,
        existing_positions=existing,
        portfolio_value=50_000.0,
        ticker="NKE",
        sector="consumer",
    )
    assert result.amount_usd <= 50.0 + 1e-6


def test_drawdown_guard_reduces_allocation() -> None:
    base = allocator.compute_allocation(
        probability=0.65,
        available_cash=10_000.0,
        existing_positions={},
        portfolio_value=50_000.0,
        ticker="NKE",
        sector="consumer",
    )
    guarded = allocator.compute_allocation(
        probability=0.65,
        available_cash=10_000.0,
        existing_positions={},
        portfolio_value=50_000.0,
        ticker="NKE",
        sector="consumer",
        recent_hits=[False, False, False, True, False],
    )
    assert guarded.amount_usd <= base.amount_usd

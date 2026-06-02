from app.pipeline import allocator


def test_allocation_within_bounds() -> None:
    amount, pct = allocator.compute_allocation(
        probability=0.65,
        available_cash=10_000.0,
        existing_positions={},
        portfolio_value=50_000.0,
        ticker="NKE",
        sector="consumer",
    )
    assert 100 <= amount <= 800
    assert pct < 0.08


def test_low_probability_skips() -> None:
    amount, pct = allocator.compute_allocation(
        probability=0.35,
        available_cash=10_000.0,
        existing_positions={},
        portfolio_value=50_000.0,
        ticker="NKE",
        sector="consumer",
    )
    assert amount == 0.0
    assert pct == 0.0


def test_ticker_cap_enforced() -> None:
    existing = {"NKE": 0.079 * 50_000.0}
    amount, _ = allocator.compute_allocation(
        probability=0.65,
        available_cash=10_000.0,
        existing_positions=existing,
        portfolio_value=50_000.0,
        ticker="NKE",
        sector="consumer",
    )
    assert amount <= 50.0 + 1e-6

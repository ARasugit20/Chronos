MAX_TICKER_PCT = 0.08
MAX_SECTOR_PCT = 0.25
KELLY_FRACTION = 0.5


def compute_allocation(
    probability: float,
    available_cash: float,
    existing_positions: dict[str, float],
    portfolio_value: float,
    ticker: str,
    sector: str,
) -> tuple[float, float]:
    b = 1.0
    kelly_full = probability - (1 - probability) / b
    kelly = kelly_full * KELLY_FRACTION
    raw_amount = kelly * available_cash

    ticker_exposure = existing_positions.get(ticker, 0.0)
    max_ticker_amount = portfolio_value * MAX_TICKER_PCT - ticker_exposure
    amount = min(raw_amount, max_ticker_amount)

    from app.pipeline.sectors import ticker_sector

    sector_exposure = sum(
        value for key, value in existing_positions.items() if ticker_sector(key) == sector
    )
    max_sector_amount = portfolio_value * MAX_SECTOR_PCT - sector_exposure
    amount = min(amount, max_sector_amount)

    if kelly_full < 0 or amount < 10.0:
        return (0.0, 0.0)

    amount = round(amount, 2)
    pct_cash = amount / available_cash if available_cash > 0 else 0.0
    return (amount, pct_cash)

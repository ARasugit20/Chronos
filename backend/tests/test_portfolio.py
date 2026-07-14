from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.portfolio_service import get_portfolio_snapshot


@pytest.mark.asyncio
async def test_portfolio_snapshot_aggregates_exposure() -> None:
    signal_a = MagicMock()
    signal_a.ticker = "NKE"

    rec_a = MagicMock()
    rec_a.amount_usd = 500.0
    rec_a.signal = signal_a

    signal_b = MagicMock()
    signal_b.ticker = "NKE"

    rec_b = MagicMock()
    rec_b.amount_usd = 300.0
    rec_b.signal = signal_b

    mock_result = MagicMock()
    mock_result.all.return_value = [(rec_a, signal_a), (rec_b, signal_b)]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    snapshot = await get_portfolio_snapshot(mock_db)

    assert snapshot.total_deployed == 800.0
    assert snapshot.open_recommendations == 2
    assert len(snapshot.ticker_exposure) == 1
    assert snapshot.ticker_exposure[0].ticker == "NKE"
    assert snapshot.ticker_exposure[0].amount_usd == 800.0
    assert snapshot.sector_exposure["consumer"] > 0


@pytest.mark.asyncio
async def test_portfolio_snapshot_reports_concentration_and_headroom() -> None:
    rec = MagicMock(amount_usd=Decimal("2000"))
    signal = MagicMock(ticker="AAPL")
    result = MagicMock()
    result.all.return_value = [(rec, signal)]
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    with patch("app.services.portfolio_service.get_settings") as settings_mock:
        settings = settings_mock.return_value
        settings.portfolio_cash = 10_000
        settings.portfolio_value = 50_000
        settings.sector_cap_pct = 0.25
        snapshot = await get_portfolio_snapshot(db)

    assert snapshot.total_deployed == 2000
    assert snapshot.largest_position_pct == 0.04
    assert snapshot.concentration_hhi == pytest.approx(0.0016)
    assert snapshot.ticker_exposure[0].headroom_usd == 2000

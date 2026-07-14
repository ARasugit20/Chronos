from unittest.mock import AsyncMock, MagicMock

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

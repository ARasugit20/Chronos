from unittest.mock import AsyncMock, MagicMock

import pytest

from app.pipeline.backtest import run_backtest


@pytest.mark.asyncio
async def test_backtest_empty() -> None:
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await run_backtest(mock_db, ml_min_outcomes=50)
    assert result.total_resolved == 0
    assert result.hit_rate == 0.0
    assert result.ml_ready is False
    assert result.paper_trading is True

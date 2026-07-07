from unittest.mock import AsyncMock, MagicMock

import pytest

from app.pipeline.backtest import run_outcome_metrics


@pytest.mark.asyncio
async def test_outcome_metrics_empty() -> None:
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await run_outcome_metrics(mock_db, ml_min_outcomes=50)
    assert result.total_resolved == 0
    assert result.hit_rate == 0.0
    assert result.ml_ready is False
    assert result.methodology == "resolved_outcome_metrics"
    assert "not a point-in-time" in result.note

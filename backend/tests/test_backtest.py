from unittest.mock import AsyncMock, MagicMock

import pytest

from app.pipeline.backtest import maximum_drawdown, run_outcome_metrics, wilson_interval


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


def test_wilson_interval_contains_observed_hit_rate() -> None:
    low, high = wilson_interval(7, 10)
    assert low < 0.7 < high
    assert 0 <= low <= high <= 1


def test_maximum_drawdown_uses_compounded_equity_curve() -> None:
    assert maximum_drawdown([0.10, -0.20, 0.05]) == pytest.approx(0.20)

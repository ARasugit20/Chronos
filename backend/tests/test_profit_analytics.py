import pytest

from app.pipeline.backtest import _profit_metrics


def test_profit_metrics_basic() -> None:
    returns = [0.05, -0.02, 0.03, -0.01, 0.04]
    hits = [1, 0, 1, 0, 1]
    expectancy, profit_factor, mean_win, mean_loss = _profit_metrics(returns, hits)
    assert expectancy == pytest.approx(sum(returns) / len(returns))
    assert profit_factor > 0
    assert mean_win > 0
    assert mean_loss < 0


def test_profit_metrics_no_losses() -> None:
    returns = [0.05, 0.03, 0.04]
    hits = [1, 1, 1]
    _, profit_factor, _, _ = _profit_metrics(returns, hits)
    assert profit_factor == pytest.approx(0.12)


def test_profit_metrics_empty() -> None:
    expectancy, profit_factor, mean_win, mean_loss = _profit_metrics([], [])
    assert expectancy == 0.0
    assert profit_factor == 0.0
    assert mean_win == 0.0
    assert mean_loss == 0.0

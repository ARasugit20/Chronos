from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.pipeline.train_stub import RetrainReport, run_model_retrain


def _make_outcome(resolved_at: datetime, hit: bool, raw_prob: float = 0.6) -> MagicMock:
    event = MagicMock()
    event.source = "sports_mock"
    event.event_type = "sports"
    event.title = "Test event"
    event.occurred_at = resolved_at - timedelta(days=1)

    signal = MagicMock()
    signal.event = event
    signal.probability_raw = raw_prob

    rec = MagicMock()
    rec.signal = signal

    outcome = MagicMock()
    outcome.resolved_at = resolved_at
    outcome.hit_boolean = hit
    outcome.recommendation = rec
    return outcome


@pytest.mark.asyncio
async def test_retrain_uses_temporal_split_and_oos_metrics() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        _make_outcome(base + timedelta(days=i * 10), hit=i % 2 == 0, raw_prob=0.55 + (i % 3) * 0.05)
        for i in range(20)
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = rows

    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_db
    mock_session.__aexit__.return_value = None

    with (
        patch("app.pipeline.train_stub.SessionLocal", return_value=mock_session),
        patch("app.pipeline.train_stub.LightGBMScorer.train", return_value=0.21) as train_mock,
    ):
        report = await run_model_retrain()

    assert isinstance(report, RetrainReport)
    assert report.train_samples >= 8
    assert report.calibrate_samples >= 1
    assert report.test_samples >= 1
    assert report.train_brier == 0.21
    assert report.oos_hit_rate is not None
    assert report.oos_brier is not None
    train_mock.assert_called_once()


@pytest.mark.asyncio
async def test_retrain_skips_when_insufficient_outcomes() -> None:
    rows = [_make_outcome(datetime(2026, 1, 1, tzinfo=UTC), hit=True)]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = rows

    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_db
    mock_session.__aexit__.return_value = None

    with patch("app.pipeline.train_stub.SessionLocal", return_value=mock_session):
        report = await run_model_retrain()

    assert report.train_samples == 1
    assert report.oos_brier is None

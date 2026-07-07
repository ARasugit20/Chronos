from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.workers.resolver_task import resolve_expired


@pytest.mark.asyncio
async def test_resolver_uses_signal_and_expiry_timestamps() -> None:
    signal_created = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    expires_at = signal_created + timedelta(days=3)

    mock_signal = MagicMock()
    mock_signal.ticker = "AAPL"
    mock_signal.created_at = signal_created
    mock_signal.probability_calibrated = 0.58

    mock_rec = MagicMock()
    mock_rec.id = uuid4()
    mock_rec.signal = mock_signal
    mock_rec.expires_at = expires_at
    mock_rec.action = "paper_buy"
    mock_rec.status = "approved"

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_rec]

    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_db
    mock_session.__aexit__.return_value = None

    with patch("app.workers.resolver_task.SessionLocal", return_value=mock_session):
        with patch("app.workers.resolver_task.get_price", new_callable=AsyncMock) as price_mock:
            price_mock.side_effect = [Decimal("100.00"), Decimal("110.00")]
            resolved = await resolve_expired()

    assert resolved == 1
    assert price_mock.await_count == 2
    price_mock.assert_any_await("AAPL", signal_created)
    price_mock.assert_any_await("AAPL", expires_at)

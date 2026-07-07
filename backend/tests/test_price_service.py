from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.prices.price_service import get_price


@pytest.mark.asyncio
async def test_polygon_price_used_when_available() -> None:
    with patch("app.prices.price_service.get_settings") as settings_mock:
        settings_mock.return_value.polygon_api_key = "test-key"
        with patch("app.prices.price_service.get_polygon_client") as client_mock:
            client_mock.return_value.get_close_price = AsyncMock(return_value=123.45)
            price = await get_price("AAPL", date(2026, 6, 1))
    assert float(price) == 123.45


@pytest.mark.asyncio
async def test_mock_fallback_without_api_key() -> None:
    with patch("app.prices.price_service.get_settings") as settings_mock:
        settings_mock.return_value.polygon_api_key = ""
        price = await get_price("AAPL", date(2026, 6, 1))
    assert 50 <= float(price) <= 500


@pytest.mark.asyncio
async def test_mock_price_is_deterministic_for_ticker_and_date() -> None:
    with patch("app.prices.price_service.get_settings") as settings_mock:
        settings_mock.return_value.polygon_api_key = ""
        first = await get_price("AAPL", date(2026, 6, 1))
        second = await get_price("AAPL", date(2026, 6, 1))
    assert first == second


@pytest.mark.asyncio
async def test_mock_price_differs_across_dates() -> None:
    with patch("app.prices.price_service.get_settings") as settings_mock:
        settings_mock.return_value.polygon_api_key = ""
        entry = await get_price("AAPL", datetime(2026, 6, 1, tzinfo=timezone.utc))
        exit_price = await get_price("AAPL", datetime(2026, 6, 4, tzinfo=timezone.utc))
    assert entry != exit_price

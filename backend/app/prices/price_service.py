# WHY: Unified price lookup with Polygon primary and deterministic mock fallback.

from __future__ import annotations

import hashlib
import random
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import structlog

from app.config import get_settings
from app.prices.polygon_client import PriceUnavailableError, get_polygon_client

logger = structlog.get_logger(__name__)

price_fetches_total: Any = None
try:
    from prometheus_client import Counter

    price_fetches_total = Counter("price_fetches_total", "Price fetches", ["source"])
except Exception:  # noqa: BLE001
    price_fetches_total = None


class HistoricalPriceUnavailableError(RuntimeError):
    pass


def _as_of_date(as_of: date | datetime | None) -> date:
    if as_of is None:
        return datetime.now(UTC).date()
    if isinstance(as_of, datetime):
        return as_of.date()
    return as_of


def _deterministic_mock_price(ticker: str, as_of: date) -> Decimal:
    """Return a stable mock close for ticker+date so resolver/backtests are reproducible."""
    seed = int(hashlib.sha256(f"{ticker.upper()}:{as_of.isoformat()}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    return Decimal(str(round(rng.uniform(50, 500), 4)))


async def get_price(ticker: str, as_of: date | datetime | None = None) -> Decimal:
    settings = get_settings()
    price_date = _as_of_date(as_of)
    if settings.polygon_api_key:
        try:
            value = await get_polygon_client().get_close_price(ticker, price_date.isoformat())
            if value is not None:
                if price_fetches_total:
                    price_fetches_total.labels(source="polygon").inc()
                logger.info("price.polygon", ticker=ticker, as_of=price_date.isoformat(), price=value)
                return Decimal(str(value))
        except PriceUnavailableError as exc:
            logger.warning("price.polygon_unavailable", ticker=ticker, as_of=price_date.isoformat(), error=str(exc))

    production_requires_live_price = (
        settings.environment == "production"
        and settings.price_source != "mock"
        and not settings.allow_mock_price_fallback
    )
    if production_requires_live_price:
        raise HistoricalPriceUnavailableError(
            f"no live historical price for {ticker} at {price_date.isoformat()}"
        )

    if price_fetches_total:
        price_fetches_total.labels(source="mock").inc()
    mock = _deterministic_mock_price(ticker, price_date)
    logger.info("price.mock_fallback", ticker=ticker, as_of=price_date.isoformat(), price=str(mock))
    return mock

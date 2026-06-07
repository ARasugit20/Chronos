# WHY: Unified price lookup with Polygon primary and mock fallback.

from __future__ import annotations

import random
from datetime import date
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


async def get_price(ticker: str, as_of: date | None = None) -> Decimal:
    settings = get_settings()
    as_of = as_of or date.today()
    if settings.polygon_api_key:
        try:
            value = await get_polygon_client().get_close_price(ticker, as_of.isoformat())
            if value is not None:
                if price_fetches_total:
                    price_fetches_total.labels(source="polygon").inc()
                logger.info("price.polygon", ticker=ticker, price=value)
                return Decimal(str(value))
        except PriceUnavailableError as exc:
            logger.warning("price.polygon_unavailable", error=str(exc))

    if price_fetches_total:
        price_fetches_total.labels(source="mock").inc()
    mock = round(random.uniform(50, 500), 4)
    logger.info("price.mock_fallback", ticker=ticker, price=mock)
    return Decimal(str(mock))

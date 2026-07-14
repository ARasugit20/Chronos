# WHY: Async Polygon.io client for historical close prices.

from __future__ import annotations

import httpx
import structlog
from datetime import date, timedelta

from app.config import get_settings

logger = structlog.get_logger(__name__)


class PriceUnavailableError(Exception):
    pass


class PolygonClient:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def get_close_price(self, ticker: str, date: str) -> float | None:
        if not self._api_key:
            raise PriceUnavailableError("missing API key")
        requested = date_from_iso(date)
        start = requested - timedelta(days=7)
        url = (
            f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start.isoformat()}/{date}"
            f"?apiKey={self._api_key}"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
        if response.status_code != 200:
            raise PriceUnavailableError(f"polygon status {response.status_code}")
        payload = response.json()
        results = payload.get("results") or []
        if not results:
            return None
        return float(results[-1]["c"])


def date_from_iso(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise PriceUnavailableError(f"invalid price date: {value}") from exc


def get_polygon_client() -> PolygonClient:
    return PolygonClient(get_settings().polygon_api_key)

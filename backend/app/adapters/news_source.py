from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

import httpx
import structlog

from app.adapters.sports_source import EventSource, RawEventDict
from app.config import get_settings

logger = structlog.get_logger(__name__)


class NewsMockSource:
    _EVENTS: ClassVar[list[str]] = [
        "Marvel film opens to $280M domestic — franchise record",
        "New steel tariff discussion — congressional hearing",
        "AI chip export controls — updated restrictions",
    ]

    async def fetch(self) -> list[RawEventDict]:
        idx = datetime.now(UTC).minute % len(self._EVENTS)
        return [
            {
                "source": "news_mock",
                "event_type": "news",
                "title": self._EVENTS[idx],
                "occurred_at": datetime.now(UTC),
                "metadata": {"data_source": "mock"},
            }
        ]


class FinnhubNewsSource:
    """Financial news from Finnhub.io — includes related tickers in payload."""

    def __init__(self, api_key: str, base_url: str = "https://finnhub.io/api/v1") -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    async def fetch(self) -> list[RawEventDict]:
        if not self._api_key:
            logger.warning("news.finnhub_missing_key")
            return []

        url = f"{self._base_url}/news"
        params = {"category": "general", "token": self._api_key}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, params=params)
            if response.status_code != 200:
                logger.warning("news.finnhub_error", status=response.status_code)
                return []
            articles = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("news.finnhub_fetch_failed", error=str(exc))
            return []

        events: list[RawEventDict] = []
        for article in articles[:25]:
            headline = article.get("headline", "").strip()
            if not headline:
                continue
            published = datetime.fromtimestamp(article.get("datetime", 0), tz=UTC)
            related = article.get("related", "") or ""
            tickers = [t.strip().upper() for t in related.split(",") if t.strip()]
            events.append(
                {
                    "source": "finnhub",
                    "event_type": "news",
                    "title": headline,
                    "occurred_at": published,
                    "metadata": {
                        "data_source": "finnhub",
                        "provider_id": str(article.get("id", "")),
                        "url": article.get("url", ""),
                        "publisher": article.get("source", ""),
                        "summary": article.get("summary", ""),
                        "tickers": tickers,
                        "category": article.get("category", "general"),
                    },
                }
            )
        logger.info("news.finnhub_fetched", count=len(events))
        return events


def get_news_source() -> EventSource:
    settings = get_settings()
    if settings.news_source == "finnhub" and settings.news_api_key:
        return FinnhubNewsSource(settings.news_api_key, settings.news_api_url)
    return NewsMockSource()

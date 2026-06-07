from unittest.mock import AsyncMock, patch

import pytest

from app.adapters.news_source import FinnhubNewsSource, NewsMockSource, get_news_source


@pytest.mark.asyncio
async def test_news_mock_source_returns_event() -> None:
    source = NewsMockSource()
    events = await source.fetch()
    assert len(events) == 1
    assert events[0]["event_type"] == "news"
    assert events[0]["source"] == "news_mock"


@pytest.mark.asyncio
async def test_finnhub_source_parses_articles() -> None:
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: [
        {
            "id": 12345,
            "headline": "NVIDIA beats earnings expectations",
            "datetime": 1717500000,
            "related": "NVDA,AMD",
            "source": "Reuters",
            "url": "https://example.com/nvda",
            "summary": "NVIDIA reported strong AI chip demand",
            "category": "general",
        }
    ]
    source = FinnhubNewsSource("test-key")
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        events = await source.fetch()
    assert len(events) == 1
    assert events[0]["source"] == "finnhub"
    assert events[0]["metadata"]["provider_id"] == "12345"
    assert "NVDA" in events[0]["metadata"]["tickers"]


def test_get_news_source_defaults_to_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("NEWS_SOURCE", "mock")
    monkeypatch.delenv("NEWS_API_KEY", raising=False)
    source = get_news_source()
    assert isinstance(source, NewsMockSource)
    get_settings.cache_clear()

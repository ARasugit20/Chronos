from datetime import UTC, datetime

from app.models.event import Event
from app.pipeline.theme_mapper import match_themes


def _event(title: str, metadata: dict | None = None) -> Event:
    return Event(
        source="finnhub",
        event_type="news",
        title=title,
        occurred_at=datetime.now(UTC),
        metadata_json=metadata or {},
        fingerprint_hash="entity-test",
    )


def test_entity_extraction_adds_ticker_match() -> None:
    matches = match_themes(
        _event("AI chip export controls hit NVIDIA supply chain", {"tickers": ["NVDA"]}),
        [],
    )
    assert matches
    assert matches[0].match_method == "entity"
    assert "NVDA" in matches[0].tickers

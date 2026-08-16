from datetime import UTC, datetime

from app.models.event import Event
from app.models.theme_mapping import ThemeMapping
from app.pipeline.theme_mapper import match_themes


def _event(title: str) -> Event:
    return Event(
        source="sports_mock",
        event_type="sports",
        title=title,
        occurred_at=datetime.now(UTC),
        metadata_json={},
        fingerprint_hash="theme-test",
    )


def test_regex_match_for_world_cup() -> None:
    mapping = ThemeMapping(
        event_pattern="world cup|fifa",
        tickers=["NKE"],
        rationale="soccer tournament sponsor exposure",
        confidence_prior=0.62,
        approved_by_human=True,
    )
    matches = match_themes(_event("FIFA World Cup 2026 host cities"), [mapping])
    assert matches
    assert matches[0].match_method in {"regex", "regex+embedding"}


def test_embedding_can_match_fed_language() -> None:
    mapping = ThemeMapping(
        event_pattern="zzz_unlikely_pattern",
        tickers=["QQQ"],
        rationale="federal reserve interest rate decision macro",
        confidence_prior=0.51,
        approved_by_human=True,
    )
    matches = match_themes(_event("Federal Reserve holds rates with dovish language"), [mapping])
    assert matches
    assert matches[0].confidence > 0

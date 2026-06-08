from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.theme_mapping import ThemeMapping
from app.pipeline.features import extract_features
from app.pipeline.scorer import LightGBMScorer, RulesScorer
from app.services.pipeline_service import process_event_signals


@pytest.mark.asyncio
async def test_rules_scorer_recency_boost() -> None:
    theme = ThemeMapping(
        event_pattern="world cup",
        tickers=["NKE"],
        rationale="test",
        confidence_prior=0.55,
        approved_by_human=True,
    )
    event = Event(
        source="sports_mock",
        event_type="sports",
        title="FIFA World Cup 2026 test",
        occurred_at=datetime.now(timezone.utc),
        metadata_json={},
        fingerprint_hash="abc",
    )
    score = RulesScorer().score(event, theme)
    assert score >= theme.confidence_prior


@pytest.mark.asyncio
async def test_suppressed_signal_no_recommendation(db_session: AsyncSession) -> None:
    theme = ThemeMapping(
        event_pattern="unknown",
        tickers=["NKE"],
        rationale="test",
        confidence_prior=0.40,
        approved_by_human=True,
    )
    db_session.add(theme)
    event = Event(
        source="news_mock",
        event_type="news",
        title="unknown event pattern",
        occurred_at=datetime.now(timezone.utc),
        metadata_json={},
        fingerprint_hash="def",
    )
    db_session.add(event)
    await db_session.flush()
    await process_event_signals(db_session, event)
    await db_session.commit()
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.signal import Signal

    event = (
        await db_session.execute(
            select(Event)
            .options(selectinload(Event.signals).selectinload(Signal.recommendation))
            .where(Event.id == event.id)
        )
    ).scalar_one()
    assert len(event.signals) == 1
    assert event.signals[0].suppressed is True
    assert event.signals[0].recommendation is None


def test_feature_extraction_keys() -> None:
    theme = ThemeMapping(
        event_pattern="fed|fomc",
        tickers=["QQQ"],
        rationale="macro",
        confidence_prior=0.5,
        approved_by_human=True,
    )
    event = Event(
        source="macro_mock",
        event_type="macro",
        title="Federal Reserve holds rates",
        occurred_at=datetime.now(timezone.utc),
        metadata_json={},
        fingerprint_hash="feat",
    )
    features = extract_features(event, theme)
    assert "hour_of_day" in features
    assert "source_trust" in features


def test_lightgbm_fallback_without_model() -> None:
    theme = ThemeMapping(
        event_pattern="nba",
        tickers=["DIS"],
        rationale="sports",
        confidence_prior=0.58,
        approved_by_human=True,
    )
    event = Event(
        source="sports_mock",
        event_type="sports",
        title="NBA Finals Game 7",
        occurred_at=datetime.now(timezone.utc),
        metadata_json={},
        fingerprint_hash="lgbm",
    )
    scorer = LightGBMScorer(model_path="/tmp/no_such_lgbm_model.pkl")
    score = scorer.score(event, theme)
    assert 0.0 <= score <= 1.0

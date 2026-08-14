from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.theme_mapping import ThemeMapping
from app.services.pipeline_service import process_event_signals
from app.models.event import Event


@pytest.mark.asyncio
async def test_pipeline_persists_lead_fields(db_session: AsyncSession) -> None:
    db_session.add(
        ThemeMapping(
            event_pattern="oil price|crude oil|opec",
            tickers=["XOM"],
            rationale="energy supply shock",
            confidence_prior=0.62,
            approved_by_human=True,
        )
    )
    await db_session.commit()

    event = Event(
        source="news_mock",
        event_type="news",
        title="OPEC cuts crude oil supply amid geopolitical tension",
        occurred_at=datetime.now(timezone.utc),
        metadata_json={},
        fingerprint_hash="lead-fields",
    )
    db_session.add(event)
    await db_session.flush()
    await process_event_signals(db_session, event)
    await db_session.commit()

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.recommendation import Recommendation
    from app.models.signal import Signal

    rec = (
        await db_session.execute(
            select(Recommendation)
            .join(Signal, Recommendation.signal_id == Signal.id)
            .options(selectinload(Recommendation.signal))
            .where(Signal.event_id == event.id)
        )
    ).scalars().first()
    assert rec is not None
    assert rec.regime is not None
    assert rec.theme_bucket == "ENERGY_SHOCK"
    assert rec.thesis is not None
    assert rec.invalidate_if is not None
    assert rec.rank_score is not None
    assert rec.calibrated_p is not None
    assert rec.action in {"paper_buy", "skip"}


@pytest.mark.asyncio
async def test_clustered_headlines_merge_without_orphan_signal(db_session: AsyncSession) -> None:
    db_session.add(
        ThemeMapping(
            event_pattern="oil price|crude oil|opec",
            tickers=["XOM"],
            rationale="energy supply shock",
            confidence_prior=0.62,
            approved_by_human=True,
        )
    )
    await db_session.commit()

    first_title = "OPEC cuts crude oil supply amid geopolitical tension"
    second_title = "Crude oil price spikes on OPEC supply cut"

    first_event = Event(
        source="news_mock",
        event_type="news",
        title=first_title,
        occurred_at=datetime.now(timezone.utc),
        metadata_json={},
        fingerprint_hash="cluster-first",
    )
    db_session.add(first_event)
    await db_session.flush()
    await process_event_signals(db_session, first_event)
    await db_session.commit()

    second_event = Event(
        source="news_mock",
        event_type="news",
        title=second_title,
        occurred_at=datetime.now(timezone.utc),
        metadata_json={},
        fingerprint_hash="cluster-second",
    )
    db_session.add(second_event)
    await db_session.flush()
    await process_event_signals(db_session, second_event)
    await db_session.commit()

    from sqlalchemy import func, select
    from sqlalchemy.orm import selectinload

    from app.models.recommendation import Recommendation
    from app.models.signal import Signal

    rec_count = (
        await db_session.execute(
            select(func.count())
            .select_from(Recommendation)
            .join(Signal, Recommendation.signal_id == Signal.id)
            .where(Signal.ticker == "XOM")
        )
    ).scalar_one()
    signal_count = (
        await db_session.execute(
            select(func.count()).select_from(Signal).where(Signal.ticker == "XOM")
        )
    ).scalar_one()

    rec = (
        await db_session.execute(
            select(Recommendation)
            .join(Signal, Recommendation.signal_id == Signal.id)
            .options(selectinload(Recommendation.signal))
            .where(Signal.ticker == "XOM")
        )
    ).scalars().first()

    assert rec_count == 1
    assert signal_count == 1
    assert rec is not None
    assert rec.evidence is not None
    assert first_title in rec.evidence
    assert second_title in rec.evidence


@pytest.mark.asyncio
async def test_recommendations_api_exposes_lead_fields(client: AsyncClient, db_session: AsyncSession) -> None:
    from app.config import get_settings

    settings = get_settings()
    db_session.add(
        ThemeMapping(
            event_pattern="oil price|crude oil|opec",
            tickers=["XOM"],
            rationale="energy",
            confidence_prior=0.62,
            approved_by_human=True,
        )
    )
    await db_session.commit()

    token_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": settings.admin_username, "password": settings.admin_password},
    )
    token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ingest = await client.post(
        "/api/v1/events/ingest",
        headers=headers,
        json={
            "source": "manual",
            "event_type": "news",
            "title": "Crude oil price spikes on OPEC supply cut",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {},
        },
    )
    assert ingest.status_code == 201

    recs = await client.get("/api/v1/recommendations")
    assert recs.status_code == 200
    data = recs.json()["data"]
    assert data
    first = data[0]
    assert "regime" in first
    assert "thesis" in first
    assert "rank_score" in first
    assert "theme_bucket" in first

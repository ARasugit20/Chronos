from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.theme_mapping import ThemeMapping


@pytest.mark.asyncio
async def test_ingest_creates_event(client: AsyncClient, db_session: AsyncSession) -> None:
    db_session.add(
        ThemeMapping(
            event_pattern="fifa|world cup",
            tickers=["NKE"],
            rationale="soccer",
            confidence_prior=0.62,
            approved_by_human=True,
        )
    )
    await db_session.commit()

    payload = {
        "source": "manual",
        "event_type": "sports",
        "title": "FIFA World Cup 2026 test",
        "occurred_at": "2026-06-02T00:00:00Z",
        "metadata": {},
    }
    first = await client.post("/api/v1/events/ingest", json=payload)
    assert first.status_code == 201
    body = first.json()
    assert body["is_duplicate"] is False
    assert body["id"] is not None

    second = await client.post("/api/v1/events/ingest", json=payload)
    assert second.status_code == 200
    assert second.json()["is_duplicate"] is True


@pytest.mark.asyncio
async def test_recommendations_include_disclaimer(client: AsyncClient, db_session: AsyncSession) -> None:
    db_session.add(
        ThemeMapping(
            event_pattern="fifa|world cup",
            tickers=["NKE"],
            rationale="soccer",
            confidence_prior=0.62,
            approved_by_human=True,
        )
    )
    await db_session.commit()

    await client.post(
        "/api/v1/events/ingest",
        json={
            "source": "manual",
            "event_type": "sports",
            "title": "FIFA World Cup 2026 ingest",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {},
        },
    )
    response = await client.get("/api/v1/recommendations")
    assert response.status_code == 200
    items = response.json()
    for item in items:
        assert "disclaimer" in item

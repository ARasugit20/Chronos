from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.theme_mapping import ThemeMapping


@pytest.mark.asyncio
async def test_full_smoke_flow(client: AsyncClient, db_session: AsyncSession) -> None:
    from app.config import get_settings

    settings = get_settings()
    db_session.add(
        ThemeMapping(
            event_pattern="nba finals|basketball",
            tickers=["NKE", "DIS"],
            rationale="NBA",
            confidence_prior=0.58,
            approved_by_human=True,
        )
    )
    await db_session.commit()

    token_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ingest = await client.post(
        "/api/v1/events/ingest",
        headers=headers,
        json={
            "source": "manual",
            "event_type": "sports",
            "title": "NBA Finals — Game 7 primetime smoke",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {},
        },
    )
    assert ingest.status_code == 201

    dup = await client.post(
        "/api/v1/events/ingest",
        headers=headers,
        json={
            "source": "manual",
            "event_type": "sports",
            "title": "NBA Finals — Game 7 primetime smoke",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {},
        },
    )
    assert dup.status_code == 200
    assert dup.json()["is_duplicate"] is True

    signals = await client.get("/api/v1/signals/live")
    assert signals.status_code == 200
    assert len(signals.json()["data"]) >= 1

    recs = await client.get("/api/v1/recommendations")
    assert recs.status_code == 200
    data = recs.json()["data"]
    assert data
    assert "disclaimer" in data[0]

    rec_id = data[0]["id"]
    approved = await client.post(f"/api/v1/recommendations/{rec_id}/approve", headers=headers)
    assert approved.status_code == 200

    audit = await client.get(f"/api/v1/audit/{rec_id}")
    assert audit.status_code == 200
    assert audit.json()["recommendation"]["id"] == rec_id

    health = await client.get("/api/v1/health")
    assert health.status_code == 200

    metrics = await client.get("/metrics")
    assert metrics.status_code == 200
    assert "events_ingested_total" in metrics.text

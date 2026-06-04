from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.theme_mapping import ThemeMapping


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    from app.config import get_settings

    settings = get_settings()
    token_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": settings.admin_username, "password": settings.admin_password},
    )
    token = token_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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
    headers = await _auth_headers(client)
    first = await client.post("/api/v1/events/ingest", json=payload, headers=headers)
    assert first.status_code == 201
    body = first.json()
    assert body["is_duplicate"] is False
    assert body["id"] is not None

    second = await client.post("/api/v1/events/ingest", json=payload, headers=headers)
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

    headers = await _auth_headers(client)
    await client.post(
        "/api/v1/events/ingest",
        headers=headers,
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
    items = response.json()["data"]
    for item in items:
        assert "disclaimer" in item

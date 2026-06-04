import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.signal import Signal


@pytest.mark.asyncio
async def test_signal_cursor_pagination(client: AsyncClient, db_session: AsyncSession) -> None:
    event = Event(
        source="manual",
        event_type="sports",
        title="pagination seed",
        occurred_at=datetime.now(timezone.utc),
        metadata_json={},
        fingerprint_hash=str(uuid.uuid4()),
    )
    db_session.add(event)
    await db_session.flush()
    for i in range(55):
        db_session.add(
            Signal(
                event_id=event.id,
                ticker=f"T{i}",
                probability_raw=0.6,
                probability_calibrated=0.6,
                horizon_hours=72,
                model_version="rules-v1",
                confidence_bucket="medium",
                suppressed=False,
            )
        )
    await db_session.commit()

    first = await client.get("/api/v1/signals/live", params={"limit": 50})
    assert first.status_code == 200
    body = first.json()
    assert len(body["data"]) == 50
    assert body["has_more"] is True
    assert body["next_cursor"] is not None

    second = await client.get("/api/v1/signals/live", params={"limit": 50, "cursor": body["next_cursor"]})
    second_body = second.json()
    assert len(second_body["data"]) == 5
    assert second_body["has_more"] is False

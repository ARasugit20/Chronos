from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.pipeline.dedup import compute_fingerprint, is_duplicate, mark_fingerprint_seen
from app.redis_client import get_redis


@pytest.mark.asyncio
async def test_duplicate_fingerprint(db_session: AsyncSession) -> None:
    redis = get_redis()
    await redis.flushdb()
    occurred = datetime(2026, 6, 2, tzinfo=timezone.utc)
    fp = compute_fingerprint("manual", "sports", "FIFA test", occurred.date())

    assert await is_duplicate(fp, redis, db_session) is False
    db_session.add(
        Event(
            source="manual",
            event_type="sports",
            title="FIFA test",
            occurred_at=occurred,
            metadata_json={},
            fingerprint_hash=fp,
        )
    )
    await db_session.commit()
    await mark_fingerprint_seen(fp, redis)

    assert await is_duplicate(fp, redis, db_session) is True
    count = (await db_session.execute(select(func.count()).select_from(Event))).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_new_fingerprint_creates_row(db_session: AsyncSession) -> None:
    redis = get_redis()
    await redis.flushdb()
    occurred = datetime(2026, 6, 3, tzinfo=timezone.utc)
    fp = compute_fingerprint("manual", "sports", "Unique", occurred.date())
    assert await is_duplicate(fp, redis, db_session) is False

import hashlib
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event

DEDUP_TTL_SECONDS = 48 * 60 * 60


def compute_fingerprint(source: str, event_type: str, title: str, occurred_date: date) -> str:
    payload = f"{source}|{event_type}|{title.lower().strip()}|{occurred_date.isoformat()}"
    return hashlib.sha256(payload.encode()).hexdigest()


async def is_duplicate(fingerprint: str, redis_client, db_session: AsyncSession) -> bool:
    redis_key = f"dedup:{fingerprint}"
    if await redis_client.exists(redis_key):
        return True

    result = await db_session.execute(select(Event.id).where(Event.fingerprint_hash == fingerprint))
    if result.scalar_one_or_none() is not None:
        await redis_client.set(redis_key, "1", ex=DEDUP_TTL_SECONDS)
        return True

    return False


async def mark_fingerprint_seen(fingerprint: str, redis_client) -> None:
    await redis_client.set(f"dedup:{fingerprint}", "1", ex=DEDUP_TTL_SECONDS)

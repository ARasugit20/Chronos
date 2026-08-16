# WHY: Production health checks for stale ingestion, mock prices, and worker liveness.

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.event import Event
from app.redis_client import get_redis

logger = structlog.get_logger(__name__)


async def check_system_health(db: AsyncSession) -> dict[str, object]:
    settings = get_settings()
    redis = get_redis()
    alerts: list[str] = []

    worker_ok = bool(await redis.get("worker:heartbeat"))
    if not worker_ok:
        alerts.append("worker_heartbeat_missing")

    last_ingest = (
        await db.execute(select(func.max(Event.created_at)))
    ).scalar_one_or_none()
    ingest_stale = False
    if last_ingest is None:
        ingest_stale = True
        alerts.append("no_events_ingested")
    else:
        last_ts = last_ingest if last_ingest.tzinfo else last_ingest.replace(tzinfo=UTC)
        age = datetime.now(UTC) - last_ts
        if age > timedelta(minutes=settings.stale_ingest_minutes):
            ingest_stale = True
            alerts.append("ingest_stale")

    mock_price_mode = settings.price_source == "mock"
    live_price_ready = not mock_price_mode
    if settings.environment == "production" and mock_price_mode:
        alerts.append("mock_prices_in_production")

    mock_news_mode = settings.news_source == "mock"
    live_news_ready = not mock_news_mode and bool(settings.news_api_key)
    if settings.environment == "production" and mock_news_mode:
        alerts.append("mock_news_in_production")
    if settings.environment == "production" and settings.news_source != "mock" and not settings.news_api_key:
        alerts.append("news_api_key_missing")

    status = "degraded" if alerts else "healthy"
    return {
        "status": status,
        "environment": settings.environment,
        "worker": worker_ok,
        "ingest_stale": ingest_stale,
        "last_ingest_at": last_ingest.isoformat() if last_ingest else None,
        "news_source": settings.news_source,
        "price_source": settings.price_source,
        "mock_price_mode": mock_price_mode,
        "mock_news_mode": mock_news_mode,
        "live_price_ready": live_price_ready,
        "live_news_ready": live_news_ready,
        "paper_trading_mode": settings.paper_trading_mode,
        "frontend_url": settings.frontend_url,
        "alerts": alerts,
    }

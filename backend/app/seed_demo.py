# WHY: End-to-end demo seed injecting events for all five themes.

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import structlog

from app.database import SessionLocal
from app.redis_client import get_redis
from app.seeds.seed import seed_theme_mappings
from app.services.pipeline_service import ingest_event

logger = structlog.get_logger(__name__)

DEMO_EVENTS = [
    ("sports_mock", "sports", "FIFA World Cup 2026 — Host cities confirmed"),
    ("sports_mock", "sports", "NBA Finals — Game 7 primetime"),
    ("macro_mock", "macro", "Federal Reserve holds rates — dovish language"),
    ("sports_mock", "sports", "Super Bowl LX — 2 weeks out"),
    ("sports_mock", "sports", "Olympics 2028 — LA venue announcement"),
]


async def run_demo_seed() -> None:
    await seed_theme_mappings()
    redis = get_redis()
    async with SessionLocal() as db:
        print("theme | ticker | calibrated | amount_usd | status")
        for source, event_type, title in DEMO_EVENTS:
            event, _, dup = await ingest_event(
                db=db,
                redis_client=redis,
                source=source,
                event_type=event_type,
                title=title,
                occurred_at=datetime.now(UTC),
                metadata={"demo": True},
            )
            if dup or event is None:
                print(f"{title[:20]} | - | - | - | duplicate")
                continue
            for signal in event.signals:
                rec = signal.recommendation
                amount = rec.amount_usd if rec else 0
                print(
                    f"{title[:20]} | {signal.ticker} | {signal.probability_calibrated:.2f} | "
                    f"{amount} | {'suppressed' if signal.suppressed else 'ok'}"
                )
    logger.info("seed_demo.completed")


if __name__ == "__main__":
    asyncio.run(run_demo_seed())

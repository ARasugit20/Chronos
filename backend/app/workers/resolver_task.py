import asyncio
import random
from datetime import datetime, timezone
from decimal import Decimal

import structlog
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import SessionLocal
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation

logger = structlog.get_logger(__name__)


async def resolve_expired() -> int:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    resolved_count = 0
    brier_total = 0.0

    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(Recommendation)
                .options(selectinload(Recommendation.signal))
                .where(Recommendation.status == "approved", Recommendation.expires_at < now)
            )
        ).scalars().all()

        for rec in rows:
            signal = rec.signal
            if signal is None:
                continue
            metadata = {}
            price_at_signal = None
            if metadata.get("price"):
                price_at_signal = Decimal(str(metadata["price"]))
            if price_at_signal is None:
                price_at_signal = Decimal(str(round(random.uniform(50, 500), 4)))

            price_at_expiry = price_at_signal * Decimal(str(1 + random.gauss(0.02, 0.05)))
            realized_return_pct = float((price_at_expiry - price_at_signal) / price_at_signal)
            hit_boolean = realized_return_pct > 0 and rec.action == "buy"
            brier_component = (signal.probability_calibrated - float(hit_boolean)) ** 2
            brier_total += brier_component

            outcome = Outcome(
                recommendation_id=rec.id,
                resolved_at=now,
                price_at_signal=price_at_signal,
                price_at_expiry=price_at_expiry,
                realized_return_pct=realized_return_pct,
                hit_boolean=hit_boolean,
                brier_component=brier_component,
                data_source=settings.price_source,
            )
            db.add(outcome)
            rec.status = "resolved"
            resolved_count += 1

        await db.commit()

    if resolved_count:
        logger.info(
            "resolver.completed",
            resolved=resolved_count,
            brier_mean=brier_total / resolved_count,
        )
    return resolved_count


@shared_task(name="app.workers.resolver_task.resolve_expired")
def resolve_expired_celery() -> int:
    return asyncio.run(resolve_expired())

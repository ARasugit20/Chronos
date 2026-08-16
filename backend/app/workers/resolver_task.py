import asyncio
from datetime import UTC, datetime

import structlog
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import SessionLocal
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.prices.price_service import HistoricalPriceUnavailableError, get_price

logger = structlog.get_logger(__name__)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


async def resolve_expired() -> int:
    settings = get_settings()
    now = datetime.now(UTC)
    resolved_count = 0
    brier_total = 0.0

    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(Recommendation)
                .options(selectinload(Recommendation.signal))
                .outerjoin(Outcome, Outcome.recommendation_id == Recommendation.id)
                .where(
                    Recommendation.status == "approved",
                    Recommendation.expires_at < now,
                    Outcome.id.is_(None),
                )
                .with_for_update(skip_locked=True)
            )
        ).scalars().all()

        for rec in rows:
            signal = rec.signal
            if signal is None:
                continue

            signal_at = _as_utc(signal.created_at)
            expiry_at = _as_utc(rec.expires_at)
            try:
                price_at_signal = await get_price(signal.ticker, signal_at)
                price_at_expiry = await get_price(signal.ticker, expiry_at)
            except HistoricalPriceUnavailableError as exc:
                logger.warning(
                    "resolver.price_unavailable",
                    recommendation_id=str(rec.id),
                    ticker=signal.ticker,
                    error=str(exc),
                )
                continue
            if price_at_signal == 0:
                logger.warning("resolver.zero_entry_price", recommendation_id=str(rec.id), ticker=signal.ticker)
                continue

            realized_return_pct = float((price_at_expiry - price_at_signal) / price_at_signal)
            hit_boolean = realized_return_pct > 0 and rec.action in {"buy", "paper_buy"}
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

import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.event import Event
from app.models.recommendation import Recommendation
from app.models.signal import Signal
from app.models.theme_mapping import ThemeMapping
from app.pipeline.calibrator import IsotonicCalibrator
from app.pipeline.dedup import is_duplicate, mark_fingerprint_seen, resolve_fingerprint
from app.pipeline.scorer import LightGBMScorer, RulesScorer
from app.pipeline.sectors import ticker_sector
from app.pipeline.theme_mapper import match_themes
from app.metrics import events_ingested_total, pipeline_duration_seconds, signals_generated_total
from app.pipeline import allocator
from app.pipeline.quality import SignalQualityGuard
from app.ws.signal_ws import publish_signal

logger = structlog.get_logger(__name__)
quality_guard = SignalQualityGuard()
HORIZON_HOURS = 72


def confidence_bucket(probability: float) -> str:
    if probability >= 0.65:
        return "high"
    if probability >= 0.5:
        return "medium"
    return "low"


async def ingest_event(
    *,
    db: AsyncSession,
    redis_client,
    source: str,
    event_type: str,
    title: str,
    occurred_at: datetime,
    metadata: dict,
) -> tuple[Event | None, str, bool]:
    occurred_date = occurred_at.date()
    fingerprint = resolve_fingerprint(
        source=source,
        event_type=event_type,
        title=title,
        occurred_date=occurred_date,
        metadata=metadata,
    )

    if await is_duplicate(fingerprint, redis_client, db):
        events_ingested_total.labels(source=source, is_duplicate="true").inc()
        return None, fingerprint, True
    started = time.perf_counter()

    event = Event(
        source=source,
        event_type=event_type,
        title=title,
        occurred_at=occurred_at,
        metadata_json=metadata,
        fingerprint_hash=fingerprint,
    )
    db.add(event)
    await db.flush()
    await mark_fingerprint_seen(fingerprint, redis_client)

    await process_event_signals(db, event)
    await db.commit()
    await db.refresh(event)
    events_ingested_total.labels(source=source, is_duplicate="false").inc()
    pipeline_duration_seconds.observe(time.perf_counter() - started)
    return event, fingerprint, False


async def process_event_signals(db: AsyncSession, event: Event) -> None:
    settings = get_settings()
    mappings = (
        await db.execute(select(ThemeMapping).where(ThemeMapping.approved_by_human.is_(True)))
    ).scalars().all()
    matches = match_themes(event, list(mappings))
    if not matches:
        logger.info("pipeline.no_theme_match", event_id=str(event.id), title=event.title)
        return

    outcome_count = await _count_outcomes(db)
    use_ml = outcome_count >= settings.ml_min_outcomes
    scorer = LightGBMScorer(settings.model_path) if use_ml else RulesScorer()
    model_version = "lgbm-v1" if use_ml else "rules-v1"
    calibrator = IsotonicCalibrator()
    rules = RulesScorer()

    existing_recs = (
        await db.execute(
            select(Recommendation, Signal)
            .join(Signal, Recommendation.signal_id == Signal.id)
            .where(Recommendation.status.in_(["pending", "approved"]))
        )
    ).all()
    existing_positions: dict[str, float] = {}
    for rec, signal in existing_recs:
        if rec.action in {"buy", "paper_buy"}:
            existing_positions[signal.ticker] = existing_positions.get(signal.ticker, 0.0) + float(
                rec.amount_usd
            )

    for match in matches:
        for ticker in match.tickers:
            raw = scorer.score(event, match.mapping)
            calibrated = calibrator.calibrate(raw, event.event_type)
            suppressed = calibrated < settings.confidence_threshold
            suppression_reason = None
            if suppressed:
                suppression_reason = f"below threshold {settings.confidence_threshold}"

            guard_suppress, guard_reason, _stats = await quality_guard.evaluate(db, ticker)
            if guard_suppress:
                suppressed = True
                suppression_reason = guard_reason

            signal = Signal(
                event_id=event.id,
                ticker=ticker,
                probability_raw=raw,
                probability_calibrated=calibrated,
                horizon_hours=HORIZON_HOURS,
                model_version=model_version,
                confidence_bucket=confidence_bucket(calibrated),
                suppressed=suppressed,
                suppression_reason=suppression_reason,
                match_method=match.match_method,
            )
            db.add(signal)
            await db.flush()
            signals_generated_total.labels(ticker=ticker, bucket=signal.confidence_bucket).inc()
            await publish_signal(
                {
                    "id": str(signal.id),
                    "ticker": signal.ticker,
                    "probability_calibrated": signal.probability_calibrated,
                    "suppressed": signal.suppressed,
                }
            )

            if suppressed:
                logger.info("pipeline.signal_suppressed", signal_id=str(signal.id), ticker=ticker)
                continue

            allocation = allocator.compute_allocation(
                calibrated,
                settings.portfolio_cash,
                existing_positions,
                settings.portfolio_value,
                ticker,
                ticker_sector(ticker),
            )
            amount_usd = allocation.amount_usd
            pct_cash = allocation.pct_cash
            action = "buy" if amount_usd > 0 else "skip"
            expires_at = datetime.now(timezone.utc) + timedelta(hours=HORIZON_HOURS)
            reason = (
                f"{event.title} maps to {ticker} via theme '{match.mapping.event_pattern}' "
                f"(prior={match.mapping.confidence_prior:.2f}, score={calibrated:.2f})"
            )
            if settings.paper_trading_mode and action == "buy":
                action = "paper_buy"
            recommendation = Recommendation(
                signal_id=signal.id,
                action=action,
                amount_usd=Decimal(str(amount_usd)),
                pct_cash=pct_cash,
                expires_at=expires_at,
                reason=reason,
                status="pending",
                disclaimer=settings.research_disclaimer,
            )
            db.add(recommendation)
            if action == "buy":
                existing_positions[ticker] = existing_positions.get(ticker, 0.0) + amount_usd

            logger.info(
                "pipeline.recommendation_created",
                signal_id=str(signal.id),
                ticker=ticker,
                action=action,
                amount_usd=amount_usd,
            )

    _ = rules


async def _count_outcomes(db: AsyncSession) -> int:
    from app.models.outcome import Outcome
    from sqlalchemy import func

    return (
        await db.execute(select(func.count()).select_from(Outcome))
    ).scalar_one()

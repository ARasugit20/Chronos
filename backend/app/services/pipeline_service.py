import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.metrics import events_ingested_total, pipeline_duration_seconds, signals_generated_total
from app.models.event import Event
from app.models.recommendation import Recommendation
from app.models.signal import Signal
from app.models.theme_mapping import ThemeMapping
from app.pipeline import allocator
from app.pipeline.calibrator import IsotonicCalibrator
from app.pipeline.dedup import is_duplicate, mark_fingerprint_seen, resolve_fingerprint
from app.pipeline.edge import estimate_edge
from app.pipeline.lead_ranker import (
    LeadCandidate,
    apply_regime_policy,
    build_invalidate_if,
    compute_expected_value,
    compute_rank_score,
    compute_risk,
    enforce_daily_cap,
    evaluate_lead,
    find_cluster,
)
from app.pipeline.quality import SignalQualityGuard
from app.pipeline.regime import Regime, RegimeTagger
from app.pipeline.scorer import LightGBMScorer, RulesScorer
from app.pipeline.sectors import ticker_sector
from app.pipeline.theme_buckets import resolve_theme_bucket
from app.pipeline.theme_mapper import match_themes
from app.ws.signal_ws import publish_signal

logger = structlog.get_logger(__name__)
quality_guard = SignalQualityGuard()
regime_tagger = RegimeTagger()
HORIZON_HOURS = 72


def _format_allocation_reason(base_reason: str, allocation) -> str:
    kelly_note = (
        f"Kelly half={allocation.kelly_half_pct:.1%}, full={allocation.kelly_full_pct:.1%}"
    )
    if allocation.adjustment_reason:
        return f"{base_reason} | {kelly_note} | {allocation.adjustment_reason}"
    return f"{base_reason} | {kelly_note}"


def confidence_bucket(probability: float) -> str:
    if probability >= 0.65:
        return "high"
    if probability >= 0.5:
        return "medium"
    return "low"


def _build_thesis(
    *,
    event: Event,
    ticker: str,
    theme_bucket: str,
    regime_primary: str,
    calibrated: float,
) -> str:
    return (
        f"{event.title} supports {ticker} under {theme_bucket} in a {regime_primary} regime "
        f"(calibrated_p={calibrated:.2f})."
    )


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


async def _recent_hits_for_ticker(db: AsyncSession, ticker: str, limit: int = 10) -> list[bool]:
    from app.models.outcome import Outcome

    rows = (
        await db.execute(
            select(Outcome)
            .join(Recommendation, Outcome.recommendation_id == Recommendation.id)
            .join(Signal, Recommendation.signal_id == Signal.id)
            .where(Signal.ticker == ticker)
            .order_by(Outcome.resolved_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [bool(row.hit_boolean) for row in rows]


async def process_event_signals(db: AsyncSession, event: Event) -> None:
    settings = get_settings()
    as_of = datetime.now(timezone.utc)
    mappings = (
        await db.execute(select(ThemeMapping).where(ThemeMapping.approved_by_human.is_(True)))
    ).scalars().all()
    matches = match_themes(event, list(mappings))
    if not matches:
        logger.info("pipeline.no_theme_match", event_id=str(event.id), title=event.title)
        return

    regime_snapshot = regime_tagger.tag(event)
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
        theme_bucket = resolve_theme_bucket(match.mapping, event.title)
        for ticker in match.tickers:
            raw = scorer.score(event, match.mapping, as_of=as_of)
            calibrated = calibrator.calibrate(raw, event.event_type)
            effective_threshold = settings.confidence_threshold + regime_snapshot.confidence_threshold_boost
            suppressed = calibrated < effective_threshold
            suppression_reason = None
            if suppressed:
                suppression_reason = f"below threshold {effective_threshold:.2f}"

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

            recent_hits = await _recent_hits_for_ticker(db, ticker)
            edge = await estimate_edge(
                db,
                theme_bucket=theme_bucket,
                calibrated_probability=calibrated,
            )
            allocation = allocator.compute_allocation(
                calibrated,
                settings.portfolio_cash,
                existing_positions,
                settings.portfolio_value,
                ticker,
                ticker_sector(ticker),
                recent_hits=recent_hits,
                regime=regime_snapshot,
                odds_override=edge.odds,
            )
            amount_usd = allocation.amount_usd
            pct_cash = allocation.pct_cash

            horizon_hours = HORIZON_HOURS
            if regime_snapshot.primary == Regime.EARNINGS_SELLTHEBEAT:
                horizon_hours = settings.earnings_sellthebeat_horizon_hours

            expires_at = datetime.now(timezone.utc) + timedelta(hours=horizon_hours)
            thesis = _build_thesis(
                event=event,
                ticker=ticker,
                theme_bucket=theme_bucket,
                regime_primary=regime_snapshot.primary.value,
                calibrated=calibrated,
            )
            invalidate_if = build_invalidate_if(theme_bucket, regime_snapshot, ticker)
            evidence = [event.title]

            cluster = await find_cluster(
                db,
                ticker=ticker,
                window_hours=settings.cluster_window_hours,
            )
            if cluster is not None and cluster.evidence:
                evidence = list(cluster.evidence) + [event.title]
                cluster.evidence = evidence
                cluster.thesis = thesis
                cluster.calibrated_p = calibrated
                cluster.rank_score = cluster.rank_score or 0.0
                logger.info(
                    "pipeline.cluster_updated",
                    ticker=ticker,
                    cluster_id=str(cluster.id),
                    evidence_count=len(evidence),
                )
                continue

            expected_value = compute_expected_value(calibrated, edge.expected_return_pct, amount_usd)
            risk = compute_risk(calibrated, amount_usd, settings.portfolio_value)
            rank_score = compute_rank_score(
                expected_value=expected_value,
                risk=risk,
                regime=regime_snapshot,
            )
            candidate = apply_regime_policy(
                LeadCandidate(
                    ticker=ticker,
                    calibrated_p=calibrated,
                    expected_value=expected_value,
                    risk=risk,
                    rank_score=rank_score,
                    theme_bucket=theme_bucket,
                    regime=regime_snapshot,
                    thesis=thesis,
                    invalidate_if=invalidate_if,
                    evidence=evidence,
                    expires_at=expires_at,
                    kelly_half_pct=allocation.kelly_half_pct,
                    adjustment_reason=allocation.adjustment_reason,
                    amount_usd=amount_usd,
                    pct_cash=pct_cash,
                    signal_id=str(signal.id),
                )
            )

            rank_decision = evaluate_lead(candidate)
            action = rank_decision.action if rank_decision.promote else "skip"
            if settings.paper_trading_mode and action == "buy":
                action = "paper_buy"
            if settings.paper_trading_mode and rank_decision.promote:
                action = "paper_buy"

            if rank_decision.promote:
                cap_decision = await enforce_daily_cap(db, candidate=candidate)
                if not cap_decision.promote:
                    action = "skip"
                    candidate.adjustment_reason = _compose_skip_reason(
                        candidate.adjustment_reason,
                        cap_decision.reason,
                    )

            reason = (
                f"{event.title} maps to {ticker} via theme '{match.mapping.event_pattern}' "
                f"(prior={match.mapping.confidence_prior:.2f}, score={calibrated:.2f})"
            )
            rec_status = "pending"
            if action == "paper_buy" and settings.paper_auto_approve:
                rec_status = "approved"

            recommendation = Recommendation(
                signal_id=signal.id,
                action=action,
                amount_usd=Decimal(str(amount_usd if action != "skip" else 0)),
                pct_cash=pct_cash if action != "skip" else 0.0,
                expires_at=expires_at,
                reason=_format_allocation_reason(reason, allocation),
                status=rec_status,
                disclaimer=settings.research_disclaimer,
                theme_bucket=theme_bucket,
                regime=regime_snapshot.primary.value,
                regime_flags=list(regime_snapshot.flags),
                calibrated_p=calibrated,
                thesis=thesis,
                invalidate_if=invalidate_if,
                evidence=evidence,
                rank_score=candidate.rank_score,
                kelly_half_pct=allocation.kelly_half_pct,
                adjustment_reason=candidate.adjustment_reason or rank_decision.reason,
            )
            db.add(recommendation)
            if action in {"buy", "paper_buy"}:
                existing_positions[ticker] = existing_positions.get(ticker, 0.0) + amount_usd

            logger.info(
                "pipeline.recommendation_created",
                signal_id=str(signal.id),
                ticker=ticker,
                action=action,
                amount_usd=amount_usd,
                rank_score=candidate.rank_score,
                regime=regime_snapshot.primary.value,
            )

    _ = rules


def _compose_skip_reason(existing: str | None, reason: str) -> str:
    if existing:
        return f"{existing}; {reason}"
    return reason


async def _count_outcomes(db: AsyncSession) -> int:
    from app.models.outcome import Outcome
    from sqlalchemy import func

    return (
        await db.execute(select(func.count()).select_from(Outcome))
    ).scalar_one()

# WHY: Rank leads by EV/risk, cluster duplicates, and enforce daily top-K cap.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.recommendation import Recommendation
from app.models.signal import Signal
from app.pipeline.regime import Regime, RegimeSnapshot
from app.pipeline.theme_buckets import CAUTION_BUCKETS, FAVORABLE_BUCKETS


@dataclass
class LeadCandidate:
    ticker: str
    calibrated_p: float
    expected_value: float
    risk: float
    rank_score: float
    theme_bucket: str
    regime: RegimeSnapshot
    thesis: str
    invalidate_if: str
    evidence: list[str] = field(default_factory=list)
    expires_at: datetime | None = None
    kelly_half_pct: float = 0.0
    adjustment_reason: str | None = None
    amount_usd: float = 0.0
    pct_cash: float = 0.0
    signal_id: str | None = None


@dataclass(frozen=True)
class RankDecision:
    promote: bool
    action: str
    reason: str


def compute_rank_score(*, expected_value: float, risk: float, regime: RegimeSnapshot) -> float:
    safe_risk = max(risk, 1e-6)
    return expected_value / (safe_risk * regime.risk_multiplier)


def compute_expected_value(calibrated_p: float, edge_return_pct: float, amount_usd: float) -> float:
    return calibrated_p * edge_return_pct * amount_usd


def compute_risk(calibrated_p: float, amount_usd: float, portfolio_value: float) -> float:
    return (1 - calibrated_p) * amount_usd + 0.01 * portfolio_value


def build_invalidate_if(theme_bucket: str, regime: RegimeSnapshot, ticker: str) -> str:
    parts = [f"Close {ticker} if calibrated edge drops below threshold"]
    if regime.primary == Regime.EARNINGS_SELLTHEBEAT:
        parts.append("or post-earnings momentum fades within 24h")
    if theme_bucket in CAUTION_BUCKETS:
        parts.append(f"or {theme_bucket} theme deteriorates")
    if "oil_geo_shock" in regime.flags:
        parts.append("or oil/geo shock escalates without confirmation")
    return "; ".join(parts)


def evaluate_lead(candidate: LeadCandidate) -> RankDecision:
    settings = get_settings()
    effective_threshold = settings.confidence_threshold + candidate.regime.confidence_threshold_boost

    if candidate.calibrated_p < effective_threshold:
        return RankDecision(False, "skip", "below_confidence_threshold")

    if candidate.theme_bucket in CAUTION_BUCKETS and candidate.calibrated_p < settings.caution_theme_min_confidence:
        return RankDecision(False, "skip", "caution_theme_requires_higher_confidence")

    if candidate.expected_value < settings.min_ev_usd:
        return RankDecision(False, "skip", "below_ev_threshold")

    if candidate.rank_score <= 0:
        return RankDecision(False, "skip", "non_positive_rank_score")

    return RankDecision(True, "paper_buy", "ranked_lead")


async def find_cluster(
    db: AsyncSession,
    *,
    ticker: str,
    window_hours: int,
    now: datetime | None = None,
) -> Recommendation | None:
    ts = now or datetime.now(timezone.utc)
    cutoff = ts - timedelta(hours=window_hours)
    row = (
        await db.execute(
            select(Recommendation)
            .join(Signal, Recommendation.signal_id == Signal.id)
            .where(Signal.ticker == ticker)
            .where(Recommendation.created_at >= cutoff)
            .where(Recommendation.action.in_(["paper_buy", "buy"]))
            .order_by(Recommendation.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return row


async def enforce_daily_cap(
    db: AsyncSession,
    *,
    candidate: LeadCandidate,
    now: datetime | None = None,
) -> RankDecision:
    settings = get_settings()
    ts = now or datetime.now(timezone.utc)
    start_of_day = ts.replace(hour=0, minute=0, second=0, microsecond=0)

    existing = (
        await db.execute(
            select(Recommendation)
            .where(Recommendation.created_at >= start_of_day)
            .where(Recommendation.action.in_(["paper_buy", "buy"]))
            .where(Recommendation.status.in_(["pending", "approved"]))
            .order_by(Recommendation.rank_score.desc().nullslast())
        )
    ).scalars().all()

    if len(existing) < settings.max_daily_leads:
        return RankDecision(True, "paper_buy", "within_daily_cap")

    lowest = existing[-1]
    if candidate.rank_score is not None and (lowest.rank_score or 0) < candidate.rank_score:
        lowest.action = "skip"
        lowest.adjustment_reason = "displaced_by_higher_rank_lead"
        return RankDecision(True, "paper_buy", "replaced_lower_rank_lead")

    return RankDecision(False, "skip", "daily_cap_reached")


def apply_regime_policy(candidate: LeadCandidate) -> LeadCandidate:
    """Adjust rank score for Aug-2026 priors without removing guards."""
    score = candidate.rank_score
    if candidate.regime.primary == Regime.RANGE_ROTATION:
        if candidate.theme_bucket in FAVORABLE_BUCKETS:
            score *= 1.1
    if candidate.theme_bucket == "ENERGY_SHOCK" and "oil_geo_shock" in candidate.regime.flags:
        score *= 1.15
    if candidate.theme_bucket == "AI_INFRA" and candidate.regime.primary == Regime.AI_INFRA_STRESS:
        score *= 0.75
    if candidate.theme_bucket == "CONSUMER_WEAKNESS":
        score *= 0.85
    return LeadCandidate(
        ticker=candidate.ticker,
        calibrated_p=candidate.calibrated_p,
        expected_value=candidate.expected_value,
        risk=candidate.risk,
        rank_score=score,
        theme_bucket=candidate.theme_bucket,
        regime=candidate.regime,
        thesis=candidate.thesis,
        invalidate_if=candidate.invalidate_if,
        evidence=candidate.evidence,
        expires_at=candidate.expires_at,
        kelly_half_pct=candidate.kelly_half_pct,
        adjustment_reason=candidate.adjustment_reason,
        amount_usd=candidate.amount_usd,
        pct_cash=candidate.pct_cash,
        signal_id=candidate.signal_id,
    )

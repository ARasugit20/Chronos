# WHY: Estimate theme-level expected payoff / odds from resolved outcomes with shrinkage.

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation


@dataclass(frozen=True)
class EdgeEstimate:
    expected_return_pct: float
    odds: float
    sample_size: int
    source: str


async def estimate_edge(
    db: AsyncSession,
    *,
    theme_bucket: str,
    calibrated_probability: float,
) -> EdgeEstimate:
    settings = get_settings()
    rows = (
        await db.execute(
            select(Outcome.realized_return_pct, Outcome.hit_boolean, Recommendation.theme_bucket)
            .join(Recommendation, Outcome.recommendation_id == Recommendation.id)
            .where(Recommendation.theme_bucket == theme_bucket)
            .order_by(Outcome.resolved_at.desc())
            .limit(500)
        )
    ).all()

    default_odds = settings.kelly_odds
    conservative_return = (calibrated_probability * default_odds - (1 - calibrated_probability)) * 0.01

    if len(rows) < settings.edge_min_samples:
        return EdgeEstimate(
            expected_return_pct=conservative_return,
            odds=default_odds,
            sample_size=len(rows),
            source="shrinkage_default",
        )

    returns = [float(row.realized_return_pct) for row in rows]
    hits = [1 if row.hit_boolean else 0 for row in rows]
    mean_return = sum(returns) / len(returns)
    hit_rate = sum(hits) / len(hits)
    implied_odds = default_odds
    if 0 < hit_rate < 1:
        implied_odds = max(0.5, min(5.0, hit_rate / (1 - hit_rate)))

    shrink = settings.edge_shrinkage_weight
    blended_return = shrink * conservative_return + (1 - shrink) * mean_return
    blended_odds = shrink * default_odds + (1 - shrink) * implied_odds

    return EdgeEstimate(
        expected_return_pct=blended_return,
        odds=blended_odds,
        sample_size=len(rows),
        source="theme_history",
    )

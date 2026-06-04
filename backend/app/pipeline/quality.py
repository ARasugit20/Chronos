# WHY: Auto-suppress signals when historical ticker precision is poor.

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.models.signal import Signal

logger = structlog.get_logger(__name__)


class SignalQualityGuard:
    MIN_OUTCOMES = 10
    MIN_PRECISION = 0.4

    async def evaluate(self, db: AsyncSession, ticker: str) -> tuple[bool, str | None, dict[str, float]]:
        rows = (
            await db.execute(
                select(Outcome)
                .join(Recommendation, Outcome.recommendation_id == Recommendation.id)
                .join(Signal, Recommendation.signal_id == Signal.id)
                .options(selectinload(Outcome.recommendation))
                .where(Signal.ticker == ticker)
                .order_by(Outcome.resolved_at.desc())
                .limit(30)
            )
        ).scalars().all()

        if len(rows) < self.MIN_OUTCOMES:
            return False, None, {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        hits = [1 if row.hit_boolean else 0 for row in rows]
        precision = sum(hits) / len(hits)
        recall = precision
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        stats = {"precision": precision, "recall": recall, "f1": f1}

        if precision < self.MIN_PRECISION:
            reason = "low_precision_guardrail"
            logger.warning("quality.suppress", ticker=ticker, **stats, suppressed=True)
            return True, reason, stats

        logger.info("quality.pass", ticker=ticker, **stats, suppressed=False)
        return False, None, stats

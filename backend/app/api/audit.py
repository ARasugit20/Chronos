from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.models.event import Event
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.models.signal import Signal
from app.schemas.recommendation import RecommendationSchema
from app.schemas.signal import SignalSchema

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


class AuditResponse(BaseModel):
    recommendation: RecommendationSchema
    signal: SignalSchema
    event: dict
    outcome: dict | None


@router.get("/{recommendation_id}", response_model=AuditResponse)
async def audit_trail(
    recommendation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> AuditResponse:
    rec = (
        await db.execute(
            select(Recommendation)
            .options(
                selectinload(Recommendation.signal).selectinload(Signal.event),
                selectinload(Recommendation.outcome),
            )
            .where(Recommendation.id == recommendation_id)
        )
    ).scalar_one_or_none()
    if rec is None or rec.signal is None or rec.signal.event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    signal = rec.signal
    event: Event = signal.event
    outcome: Outcome | None = rec.outcome

    return AuditResponse(
        recommendation=RecommendationSchema(
            id=rec.id,
            signal_id=rec.signal_id,
            action=rec.action,
            amount_usd=rec.amount_usd,
            pct_cash=rec.pct_cash,
            expires_at=rec.expires_at,
            reason=rec.reason,
            status=rec.status,
            disclaimer=rec.disclaimer,
            created_at=rec.created_at,
            model_version=signal.model_version,
        ),
        signal=SignalSchema(
            id=signal.id,
            event_id=signal.event_id,
            ticker=signal.ticker,
            probability_raw=signal.probability_raw,
            probability_calibrated=signal.probability_calibrated,
            horizon_hours=signal.horizon_hours,
            model_version=signal.model_version,
            confidence_bucket=signal.confidence_bucket,
            suppressed=signal.suppressed,
            suppression_reason=signal.suppression_reason,
            created_at=signal.created_at,
            data_source=event.source,
        ),
        event={
            "id": str(event.id),
            "source": event.source,
            "event_type": event.event_type,
            "title": event.title,
            "occurred_at": event.occurred_at.isoformat(),
            "metadata_json": event.metadata_json,
            "fingerprint_hash": event.fingerprint_hash,
            "created_at": event.created_at.isoformat(),
        },
        outcome=None
        if outcome is None
        else {
            "id": str(outcome.id),
            "resolved_at": outcome.resolved_at.isoformat(),
            "price_at_signal": str(outcome.price_at_signal),
            "price_at_expiry": str(outcome.price_at_expiry),
            "realized_return_pct": outcome.realized_return_pct,
            "hit_boolean": outcome.hit_boolean,
            "brier_component": outcome.brier_component,
            "data_source": outcome.data_source,
        },
    )

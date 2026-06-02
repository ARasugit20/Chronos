from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.models.event import Event
from app.models.signal import Signal
from app.schemas.signal import SignalSchema

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


@router.get("/live", response_model=list[SignalSchema])
async def live_signals(
    suppressed: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> list[SignalSchema]:
    stmt = (
        select(Signal)
        .options(selectinload(Signal.event))
        .where(Signal.suppressed == suppressed)
        .order_by(Signal.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        SignalSchema(
            id=row.id,
            event_id=row.event_id,
            ticker=row.ticker,
            probability_raw=row.probability_raw,
            probability_calibrated=row.probability_calibrated,
            horizon_hours=row.horizon_hours,
            model_version=row.model_version,
            confidence_bucket=row.confidence_bucket,
            suppressed=row.suppressed,
            suppression_reason=row.suppression_reason,
            created_at=row.created_at,
            data_source=row.event.source if row.event else "mock",
        )
        for row in rows
    ]

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.models.signal import Signal
from app.schemas.pagination import CursorPage
from app.schemas.signal import SignalSchema

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


def _to_schema(row: Signal) -> SignalSchema:
    return SignalSchema(
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


@router.get("/live", response_model=CursorPage[SignalSchema])
async def live_signals(
    suppressed: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> CursorPage[SignalSchema]:
    stmt = (
        select(Signal)
        .options(selectinload(Signal.event))
        .where(Signal.suppressed == suppressed)
        .order_by(Signal.id.asc())
    )
    if cursor is not None:
        stmt = stmt.where(Signal.id > cursor)
    stmt = stmt.limit(limit + 1)
    rows = (await db.execute(stmt)).scalars().all()
    has_more = len(rows) > limit
    page_rows = rows[:limit]
    next_cursor = page_rows[-1].id if has_more and page_rows else None
    return CursorPage(
        data=[_to_schema(row) for row in page_rows],
        next_cursor=next_cursor,
        has_more=has_more,
    )

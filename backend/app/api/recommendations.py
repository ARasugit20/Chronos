from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.database import get_db_session
from app.metrics import recommendations_actioned_total
from app.models.recommendation import Recommendation
from app.schemas.pagination import CursorPage
from app.schemas.recommendation import RecommendationSchema

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("", response_model=CursorPage[RecommendationSchema])
async def list_recommendations(
    status_filter: str = Query(default="pending", alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> CursorPage[RecommendationSchema]:
    stmt = (
        select(Recommendation)
        .options(selectinload(Recommendation.signal))
        .where(Recommendation.status == status_filter)
        .order_by(Recommendation.rank_score.desc().nullslast(), Recommendation.id.asc())
    )
    if cursor is not None:
        stmt = stmt.where(Recommendation.id > cursor)
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


@router.post("/{recommendation_id}/approve", response_model=RecommendationSchema)
async def approve_recommendation(
    recommendation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: str = Depends(get_current_user),
) -> RecommendationSchema:
    rec = await _get_recommendation(db, recommendation_id)
    rec.status = "approved"
    recommendations_actioned_total.labels(action="approve").inc()
    await db.commit()
    await db.refresh(rec)
    return _to_schema(rec)


@router.post("/{recommendation_id}/skip", response_model=RecommendationSchema)
async def skip_recommendation(
    recommendation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: str = Depends(get_current_user),
) -> RecommendationSchema:
    rec = await _get_recommendation(db, recommendation_id)
    rec.status = "skipped"
    recommendations_actioned_total.labels(action="skip").inc()
    await db.commit()
    await db.refresh(rec)
    return _to_schema(rec)


async def _get_recommendation(db: AsyncSession, recommendation_id: UUID) -> Recommendation:
    rec = (
        await db.execute(
            select(Recommendation)
            .options(selectinload(Recommendation.signal))
            .where(Recommendation.id == recommendation_id)
        )
    ).scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    return rec


def _to_schema(rec: Recommendation) -> RecommendationSchema:
    return RecommendationSchema(
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
        model_version=rec.signal.model_version if rec.signal else "rules-v1",
        theme_bucket=rec.theme_bucket,
        regime=rec.regime,
        regime_flags=rec.regime_flags or [],
        calibrated_p=rec.calibrated_p,
        thesis=rec.thesis,
        invalidate_if=rec.invalidate_if,
        evidence=rec.evidence or [],
        rank_score=rec.rank_score,
        kelly_half_pct=rec.kelly_half_pct,
        adjustment_reason=rec.adjustment_reason,
    )

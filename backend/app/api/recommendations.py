from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.models.recommendation import Recommendation
from app.models.signal import Signal
from app.schemas.recommendation import RecommendationSchema

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationSchema])
async def list_recommendations(
    status_filter: str = Query(default="pending", alias="status"),
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> list[RecommendationSchema]:
    stmt = (
        select(Recommendation)
        .options(selectinload(Recommendation.signal))
        .where(Recommendation.status == status_filter)
        .order_by(Recommendation.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        RecommendationSchema(
            id=row.id,
            signal_id=row.signal_id,
            action=row.action,
            amount_usd=row.amount_usd,
            pct_cash=row.pct_cash,
            expires_at=row.expires_at,
            reason=row.reason,
            status=row.status,
            disclaimer=row.disclaimer,
            created_at=row.created_at,
            model_version=row.signal.model_version if row.signal else "rules-v1",
        )
        for row in rows
    ]


@router.post("/{recommendation_id}/approve", response_model=RecommendationSchema)
async def approve_recommendation(
    recommendation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> RecommendationSchema:
    rec = await _get_recommendation(db, recommendation_id)
    rec.status = "approved"
    await db.commit()
    await db.refresh(rec)
    return _to_schema(rec)


@router.post("/{recommendation_id}/skip", response_model=RecommendationSchema)
async def skip_recommendation(
    recommendation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> RecommendationSchema:
    rec = await _get_recommendation(db, recommendation_id)
    rec.status = "skipped"
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
    )

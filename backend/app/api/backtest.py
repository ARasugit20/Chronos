from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session
from app.pipeline.backtest import run_outcome_metrics

router = APIRouter(prefix="/api/v1", tags=["research"])


class BucketReliability(BaseModel):
    samples: float
    mean_predicted: float
    observed_hit_rate: float
    calibration_gap: float


class OutcomeMetricsResponse(BaseModel):
    methodology: str
    total_resolved: int
    hit_rate: float
    mean_brier: float
    precision_by_ticker: dict[str, float]
    bucket_reliability: dict[str, BucketReliability]
    ml_ready: bool
    paper_trading: bool
    note: str
    disclaimer: str


class BacktestResponse(OutcomeMetricsResponse):
    deprecated: bool = Field(
        default=True,
        description="Use /api/v1/outcome-metrics; /backtest is a compatibility alias.",
    )


def _to_response(result, *, settings) -> OutcomeMetricsResponse:
    return OutcomeMetricsResponse(
        methodology=result.methodology,
        total_resolved=result.total_resolved,
        hit_rate=result.hit_rate,
        mean_brier=result.mean_brier,
        precision_by_ticker=result.precision_by_ticker,
        bucket_reliability={
            bucket: BucketReliability(**values)
            for bucket, values in result.bucket_reliability.items()
        },
        ml_ready=result.ml_ready,
        paper_trading=settings.paper_trading_mode,
        note=result.note,
        disclaimer=settings.research_disclaimer,
    )


@router.get("/outcome-metrics", response_model=OutcomeMetricsResponse)
async def get_outcome_metrics(db: AsyncSession = Depends(get_db_session)) -> OutcomeMetricsResponse:
    settings = get_settings()
    result = await run_outcome_metrics(db, ml_min_outcomes=settings.ml_min_outcomes)
    return _to_response(result, settings=settings)


@router.get("/backtest", response_model=BacktestResponse, deprecated=True)
async def get_backtest_summary(db: AsyncSession = Depends(get_db_session)) -> BacktestResponse:
    settings = get_settings()
    result = await run_outcome_metrics(db, ml_min_outcomes=settings.ml_min_outcomes)
    base = _to_response(result, settings=settings)
    return BacktestResponse(**base.model_dump())

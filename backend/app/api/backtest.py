from __future__ import annotations

from fastapi import APIRouter, Depends
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session
from app.pipeline.backtest import run_outcome_metrics
from app.pipeline.replay import (
    ReplayAssumptions,
    ReplayObservation,
    run_historical_replay,
)

router = APIRouter(prefix="/api/v1", tags=["research"])


class BucketReliability(BaseModel):
    samples: float
    mean_predicted: float
    observed_hit_rate: float
    calibration_gap: float


class BreakdownStatsResponse(BaseModel):
    samples: int
    hit_rate: float
    mean_brier: float
    expectancy: float
    profit_factor: float


class OutcomeMetricsResponse(BaseModel):
    methodology: str
    total_resolved: int
    hit_rate: float
    mean_brier: float
    precision_by_ticker: dict[str, float]
    bucket_reliability: dict[str, BucketReliability]
    mean_return_pct: float
    return_volatility: float
    max_drawdown_pct: float
    calibration_error: float
    hit_rate_ci95: tuple[float, float]
    rolling_30: dict[str, float]
    ml_ready: bool
    paper_trading: bool
    note: str
    disclaimer: str
    expectancy: float = 0.0
    profit_factor: float = 0.0
    mean_win_pct: float = 0.0
    mean_loss_pct: float = 0.0
    by_confidence_bucket: dict[str, BreakdownStatsResponse] = Field(default_factory=dict)
    by_theme_bucket: dict[str, BreakdownStatsResponse] = Field(default_factory=dict)
    by_regime: dict[str, BreakdownStatsResponse] = Field(default_factory=dict)
    sector_contribution: dict[str, float] = Field(default_factory=dict)


class BacktestResponse(OutcomeMetricsResponse):
    deprecated: bool = Field(
        default=True,
        description="Use /api/v1/outcome-metrics; /backtest is a compatibility alias.",
    )


class ReplayObservationRequest(BaseModel):
    ticker: str
    signal_at: datetime
    expires_at: datetime
    entry_price: float = Field(gt=0)
    exit_price: float = Field(gt=0)
    probability: float = Field(ge=0, le=1)
    benchmark_return_pct: float = 0.0


class ReplayRequest(BaseModel):
    observations: list[ReplayObservationRequest]
    initial_cash: float = Field(default=100_000, gt=0)
    allocation_pct: float = Field(default=0.02, gt=0, le=1)
    commission_bps: float = Field(default=1.0, ge=0)
    slippage_bps: float = Field(default=5.0, ge=0)


class ReplayResponse(BaseModel):
    methodology: str
    trade_count: int
    ending_cash: float
    total_return_pct: float
    benchmark_return_pct: float
    alpha_pct: float
    hit_rate: float
    max_drawdown_pct: float


def _breakdown_to_response(data: dict) -> dict[str, BreakdownStatsResponse]:
    return {
        key: BreakdownStatsResponse(
            samples=stats.samples,
            hit_rate=stats.hit_rate,
            mean_brier=stats.mean_brier,
            expectancy=stats.expectancy,
            profit_factor=stats.profit_factor,
        )
        for key, stats in data.items()
    }


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
        mean_return_pct=result.mean_return_pct,
        return_volatility=result.return_volatility,
        max_drawdown_pct=result.max_drawdown_pct,
        calibration_error=result.calibration_error,
        hit_rate_ci95=result.hit_rate_ci95,
        rolling_30=result.rolling_30,
        ml_ready=result.ml_ready,
        paper_trading=settings.paper_trading_mode,
        note=result.note,
        disclaimer=settings.research_disclaimer,
        expectancy=result.expectancy,
        profit_factor=result.profit_factor,
        mean_win_pct=result.mean_win_pct,
        mean_loss_pct=result.mean_loss_pct,
        by_confidence_bucket=_breakdown_to_response(result.by_confidence_bucket),
        by_theme_bucket=_breakdown_to_response(result.by_theme_bucket),
        by_regime=_breakdown_to_response(result.by_regime),
        sector_contribution=result.sector_contribution,
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


@router.post("/historical-replay", response_model=ReplayResponse)
async def historical_replay(body: ReplayRequest) -> ReplayResponse:
    """Replay caller-supplied point-in-time observations with explicit costs."""
    result = run_historical_replay(
        [
            ReplayObservation(
                ticker=row.ticker,
                signal_at=row.signal_at,
                expires_at=row.expires_at,
                entry_price=row.entry_price,
                exit_price=row.exit_price,
                probability=row.probability,
                benchmark_return_pct=row.benchmark_return_pct,
            )
            for row in body.observations
        ],
        ReplayAssumptions(
            initial_cash=body.initial_cash,
            allocation_pct=body.allocation_pct,
            commission_bps=body.commission_bps,
            slippage_bps=body.slippage_bps,
        ),
    )
    return ReplayResponse(
        methodology=result.methodology,
        trade_count=len(result.trades),
        ending_cash=result.ending_cash,
        total_return_pct=result.total_return_pct,
        benchmark_return_pct=result.benchmark_return_pct,
        alpha_pct=result.alpha_pct,
        hit_rate=result.hit_rate,
        max_drawdown_pct=result.max_drawdown_pct,
    )

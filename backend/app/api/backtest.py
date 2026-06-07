from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session
from app.pipeline.backtest import run_backtest

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])


class BacktestResponse(BaseModel):
    total_resolved: int
    hit_rate: float
    mean_brier: float
    precision_by_ticker: dict[str, float]
    ml_ready: bool
    paper_trading: bool
    disclaimer: str


@router.get("", response_model=BacktestResponse)
async def get_backtest_summary(db: AsyncSession = Depends(get_db_session)) -> BacktestResponse:
    settings = get_settings()
    result = await run_backtest(db, ml_min_outcomes=settings.ml_min_outcomes)
    return BacktestResponse(
        total_resolved=result.total_resolved,
        hit_rate=result.hit_rate,
        mean_brier=result.mean_brier,
        precision_by_ticker=result.precision_by_ticker,
        ml_ready=result.ml_ready,
        paper_trading=settings.paper_trading_mode,
        disclaimer=settings.research_disclaimer,
    )

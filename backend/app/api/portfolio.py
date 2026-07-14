from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session
from app.services.portfolio_service import get_portfolio_snapshot

router = APIRouter(prefix="/api/v1", tags=["portfolio"])


class TickerExposureSchema(BaseModel):
    ticker: str
    sector: str
    amount_usd: float
    pct_portfolio: float
    pct_ticker_cap: float


class PortfolioResponse(BaseModel):
    portfolio_cash: float
    portfolio_value: float
    available_cash: float
    total_deployed: float
    pct_deployed: float
    sector_cap_pct: float
    max_ticker_pct: float
    open_recommendations: int
    ticker_exposure: list[TickerExposureSchema]
    sector_exposure: dict[str, float]
    paper_trading_mode: bool
    disclaimer: str


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(db: AsyncSession = Depends(get_db_session)) -> PortfolioResponse:
    settings = get_settings()
    snapshot = await get_portfolio_snapshot(db)
    return PortfolioResponse(
        portfolio_cash=snapshot.portfolio_cash,
        portfolio_value=snapshot.portfolio_value,
        available_cash=snapshot.available_cash,
        total_deployed=snapshot.total_deployed,
        pct_deployed=snapshot.pct_deployed,
        sector_cap_pct=snapshot.sector_cap_pct,
        max_ticker_pct=snapshot.max_ticker_pct,
        open_recommendations=snapshot.open_recommendations,
        ticker_exposure=[TickerExposureSchema(**row.__dict__) for row in snapshot.ticker_exposure],
        sector_exposure=snapshot.sector_exposure,
        paper_trading_mode=settings.paper_trading_mode,
        disclaimer=settings.research_disclaimer,
    )

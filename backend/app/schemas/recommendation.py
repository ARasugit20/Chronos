from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendationSchema(BaseModel):
    id: UUID
    signal_id: UUID
    action: str
    amount_usd: Decimal
    pct_cash: float
    expires_at: datetime
    reason: str
    status: str
    disclaimer: str
    created_at: datetime
    model_version: str = "rules-v1"
    theme_bucket: str | None = None
    regime: str | None = None
    regime_flags: list[str] = Field(default_factory=list)
    calibrated_p: float | None = None
    thesis: str | None = None
    invalidate_if: str | None = None
    evidence: list[Any] = Field(default_factory=list)
    rank_score: float | None = None
    kelly_half_pct: float | None = None
    adjustment_reason: str | None = None

    model_config = {"from_attributes": True}

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


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

    model_config = {"from_attributes": True}

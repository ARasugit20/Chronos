from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SignalSchema(BaseModel):
    id: UUID
    event_id: UUID
    ticker: str
    probability_raw: float
    probability_calibrated: float
    horizon_hours: int
    model_version: str
    confidence_bucket: str
    suppressed: bool
    suppression_reason: str | None
    created_at: datetime
    data_source: str = "mock"

    model_config = {"from_attributes": True}

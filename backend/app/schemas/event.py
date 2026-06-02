from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EventIngestRequest(BaseModel):
    source: str
    event_type: str
    title: str
    occurred_at: datetime
    metadata: dict = Field(default_factory=dict)


class EventIngestResponse(BaseModel):
    id: UUID | None = None
    fingerprint_hash: str
    is_duplicate: bool

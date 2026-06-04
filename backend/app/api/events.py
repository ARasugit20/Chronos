from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db_session
from app.redis_client import get_redis
from app.schemas.event import EventIngestRequest, EventIngestResponse
from app.services.pipeline_service import ingest_event

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("/ingest", response_model=EventIngestResponse)
async def ingest(
    body: EventIngestRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    _user: str = Depends(get_current_user),
) -> EventIngestResponse:
    redis_client = get_redis()
    event, fingerprint, duplicate = await ingest_event(
        db=db,
        redis_client=redis_client,
        source=body.source,
        event_type=body.event_type,
        title=body.title,
        occurred_at=body.occurred_at,
        metadata=body.metadata,
    )
    if duplicate:
        response.status_code = status.HTTP_200_OK
        return EventIngestResponse(id=None, fingerprint_hash=fingerprint, is_duplicate=True)
    response.status_code = status.HTTP_201_CREATED
    assert event is not None
    return EventIngestResponse(id=event.id, fingerprint_hash=fingerprint, is_duplicate=False)

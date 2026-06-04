# WHY: WebSocket feed broadcasting new signals via Redis pub/sub.

from __future__ import annotations

import asyncio
import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import SessionLocal
from app.models.signal import Signal
from app.redis_client import get_redis
from app.schemas.signal import SignalSchema

logger = structlog.get_logger(__name__)
router = APIRouter()
CHANNEL = "signals:new"


@router.websocket("/ws/signals")
async def signals_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    redis = get_redis()
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(Signal).options(selectinload(Signal.event)).order_by(Signal.created_at.desc()).limit(20)
            )
        ).scalars().all()
    payload = [_signal_payload(row) for row in rows]
    await websocket.send_json({"type": "snapshot", "data": payload})

    pubsub = redis.pubsub()
    await pubsub.subscribe(CHANNEL)

    async def heartbeat() -> None:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})

    async def listener() -> None:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            await websocket.send_json({"type": "signal", "data": json.loads(message["data"])})

    heartbeat_task = asyncio.create_task(heartbeat())
    listener_task = asyncio.create_task(listener())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        heartbeat_task.cancel()
        listener_task.cancel()
        await pubsub.unsubscribe(CHANNEL)


def _signal_payload(row: Signal) -> dict:
    schema = SignalSchema(
        id=row.id,
        event_id=row.event_id,
        ticker=row.ticker,
        probability_raw=row.probability_raw,
        probability_calibrated=row.probability_calibrated,
        horizon_hours=row.horizon_hours,
        model_version=row.model_version,
        confidence_bucket=row.confidence_bucket,
        suppressed=row.suppressed,
        suppression_reason=row.suppression_reason,
        created_at=row.created_at,
        data_source=row.event.source if row.event else "mock",
    )
    return schema.model_dump(mode="json")


async def publish_signal(signal_payload: dict) -> None:
    redis = get_redis()
    await redis.publish(CHANNEL, json.dumps(signal_payload))

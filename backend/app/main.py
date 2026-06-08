from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.api import audit, auth, backtest, events, recommendations, signals
from app.database import SessionLocal
from app.metrics import (
    ingest_stale_gauge,
    mock_news_mode_gauge,
    mock_price_mode_gauge,
    worker_heartbeat_gauge,
)
from app.services.monitoring import check_system_health
from app.config import get_settings
from app.database import engine
from app.logging_config import configure_logging
from app.middleware import RequestContextMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.ws import signal_ws
from app.redis_client import close_redis, get_redis

configure_logging()
logger = structlog.get_logger(__name__)
_metrics_instrumented = False


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    logger.info("app.startup")
    yield
    if settings.environment == "production":
        await engine.dispose()
        await close_redis()


def create_app() -> FastAPI:
    global _metrics_instrumented
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        description="Event-driven quant research pipeline: ingest → score → recommend → resolve outcomes.",
        version="0.1.0",
    )

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(events.router)
    app.include_router(signals.router)
    app.include_router(recommendations.router)
    app.include_router(audit.router)
    app.include_router(backtest.router)
    app.include_router(signal_ws.router)

    if not _metrics_instrumented:
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")
        _metrics_instrumented = True

    @app.get("/api/v1/health")
    async def healthcheck() -> dict[str, object]:
        db_ok = False
        redis_ok = False
        worker_ok = False
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception:  # noqa: BLE001
            db_ok = False

        try:
            redis = get_redis()
            redis_ok = bool(await redis.ping())
            worker_ok = bool(await redis.get("worker:heartbeat"))
        except Exception:  # noqa: BLE001
            redis_ok = False

        payload: dict[str, object] = {
            "status": "ok",
            "db": db_ok,
            "redis": redis_ok,
            "worker": worker_ok,
        }
        if db_ok:
            try:
                async with SessionLocal() as db:
                    monitoring = await check_system_health(db)
                payload["monitoring"] = monitoring
                worker_heartbeat_gauge.set(1 if monitoring["worker"] else 0)
                ingest_stale_gauge.set(1 if monitoring["ingest_stale"] else 0)
                mock_price_mode_gauge.set(1 if monitoring["mock_price_mode"] else 0)
                mock_news_mode_gauge.set(1 if monitoring["mock_news_mode"] else 0)
                if monitoring["alerts"]:
                    payload["status"] = "degraded"
            except Exception:  # noqa: BLE001
                pass
        return payload

    return app


app = create_app()

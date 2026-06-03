from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.api import audit, events, recommendations, signals
from app.config import get_settings
from app.database import engine
from app.logging_config import configure_logging
from app.middleware import RequestContextMiddleware
from app.redis_client import get_redis

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("app.startup")
    yield
    await engine.dispose()
    redis = get_redis()
    await redis.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        description="Event-driven quant research pipeline: ingest → score → recommend → resolve outcomes.",
        version="0.1.0",
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(events.router)
    app.include_router(signals.router)
    app.include_router(recommendations.router)
    app.include_router(audit.router)

    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

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

        return {"status": "ok", "db": db_ok, "redis": redis_ok, "worker": worker_ok}

    return app


app = create_app()

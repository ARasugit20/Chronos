# WHY: Redis sliding-window rate limiting per client IP.

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.redis_client import get_redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in {"/api/v1/health", "/metrics", "/docs", "/openapi.json"}:
            return await call_next(request)

        settings = get_settings()
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        window = settings.rate_limit_window_seconds
        bucket = int(time.time()) // window
        key = f"ratelimit:{client_ip}:{bucket}"

        redis = get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window)

        if count > settings.rate_limit_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "rate limit exceeded"},
                headers={"Retry-After": str(window)},
            )
        return await call_next(request)

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_rate_limit_returns_429(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "rate_limit_requests", 2)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)

    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app, lifespan="off"),
        base_url="http://test",
    ) as client:
        for _ in range(2):
            await client.get("/api/v1/signals/live")
        blocked = await client.get("/api/v1/signals/live")
    assert blocked.status_code == 429

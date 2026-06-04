import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture
def auth_client():
    app = create_app()
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_token_issuance(auth_client: AsyncClient) -> None:
    settings = get_settings()
    response = await auth_client.post(
        "/api/v1/auth/token",
        data={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


@pytest.mark.asyncio
async def test_ingest_requires_auth(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/v1/events/ingest",
        json={
            "source": "manual",
            "event_type": "sports",
            "title": "auth test",
            "occurred_at": "2026-06-02T00:00:00Z",
            "metadata": {},
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ingest_with_valid_token(auth_client: AsyncClient) -> None:
    settings = get_settings()
    token_resp = await auth_client.post(
        "/api/v1/auth/token",
        data={"username": settings.admin_username, "password": settings.admin_password},
    )
    token = token_resp.json()["access_token"]
    response = await auth_client.post(
        "/api/v1/events/ingest",
        json={
            "source": "manual",
            "event_type": "sports",
            "title": "auth bearer test unique",
            "occurred_at": "2026-06-03T00:00:00Z",
            "metadata": {},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in {200, 201}


@pytest.mark.asyncio
async def test_invalid_token_rejected(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/v1/events/ingest",
        json={
            "source": "manual",
            "event_type": "sports",
            "title": "bad token",
            "occurred_at": "2026-06-04T00:00:00Z",
            "metadata": {},
        },
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401

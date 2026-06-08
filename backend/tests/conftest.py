from collections.abc import AsyncGenerator, Generator

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.database import Base, get_db_session
from app.main import create_app
from app.redis_client import close_redis, reset_redis

pytest_plugins = ("pytest_asyncio",)

TEST_DATABASE_URL = "postgresql+asyncpg://invest:invest_local@localhost:5432/invest_agent"


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture(autouse=True)
async def _fake_redis() -> AsyncGenerator[None, None]:
    import app.redis_client as redis_module

    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    redis_module._redis = client
    yield
    await client.aclose()
    reset_redis()


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    await close_redis()
    reset_redis()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


def _build_test_app(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db
    return app


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    app = _build_test_app(db_engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    app = _build_test_app(db_engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

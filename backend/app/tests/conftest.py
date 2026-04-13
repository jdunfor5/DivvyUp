"""
Shared pytest fixtures for DivvyUp API tests.

Requires a PostgreSQL test database.  Set TEST_DATABASE_URL before running,
or ensure the default credentials match your local setup.

    createdb divvyup_test
    TEST_DATABASE_URL=postgresql+asyncpg://divvyup_user:yourpassword@localhost:5432/divvyup_test pytest
"""
import os
import uuid
from contextlib import asynccontextmanager

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL: str = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://divvyup_user:yourpassword@localhost:5432/divvyup_test",
)

# Created inside the session fixture so they share the session event loop.
_engine = None
_SessionLocal = None


@asynccontextmanager
async def _noop_lifespan(app):
    """Replace the real lifespan so tests skip the production DB startup checks."""
    yield


# ---------------------------------------------------------------------------
# Database setup / teardown — runs once per test session
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_db():
    global _engine, _SessionLocal

    _engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    _SessionLocal = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    # Register all models with SQLAlchemy metadata before create_all.
    import app.models.category      # noqa: F401
    import app.models.comment       # noqa: F401
    import app.models.expense       # noqa: F401
    import app.models.group         # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.recurring     # noqa: F401
    import app.models.settlement    # noqa: F401
    import app.models.user          # noqa: F401

    from app.dependencies.database import Base, SEED_CATEGORIES
    from app.models.category import Category
    from sqlalchemy import select

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed categories required for expense creation (FK constraint).
    async with _SessionLocal() as session:
        result = await session.execute(select(Category))
        if not result.scalars().first():
            session.add_all([Category(**c) for c in SEED_CATEGORIES])
            await session.commit()

    yield

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await _engine.dispose()


# ---------------------------------------------------------------------------
# HTTP client with test DB session injected
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(loop_scope="session")
async def client():
    """AsyncClient pointed at the test database; production lifespan is skipped."""
    from app.dependencies.database import get_session
    from app.main import app

    app.router.lifespan_context = _noop_lifespan

    async def _override_session():
        async with _SessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Reusable user / auth / group fixtures
# ---------------------------------------------------------------------------

def _unique_user_payload(**overrides) -> dict:
    tag = uuid.uuid4().hex[:8]
    return {
        "email": f"user_{tag}@test.com",
        "password": "TestPass123!",
        "display_name": f"User {tag}",
        **overrides,
    }


async def _create_and_login(client: AsyncClient) -> dict:
    """Register a user, log in, and return {payload, user, headers}."""
    payload = _unique_user_payload()

    r = await client.post("/users/", json=payload)
    assert r.status_code == 200, r.text

    token_r = await client.post(
        "/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
    )
    assert token_r.status_code == 200, token_r.text

    return {
        "payload": payload,
        "user": r.json(),
        "headers": {"Authorization": f"Bearer {token_r.json()['access_token']}"},
    }


@pytest_asyncio.fixture(loop_scope="session")
async def user_a(client: AsyncClient) -> dict:
    return await _create_and_login(client)


@pytest_asyncio.fixture(loop_scope="session")
async def user_b(client: AsyncClient) -> dict:
    return await _create_and_login(client)


@pytest_asyncio.fixture(loop_scope="session")
async def group(client: AsyncClient, user_a: dict) -> dict:
    """A group created and owned by user_a."""
    r = await client.post(
        "/groups/",
        json={"name": "Test Group", "description": "Fixture group"},
        headers=user_a["headers"],
    )
    assert r.status_code == 200, r.text
    return r.json()

import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.config import settings
from app.db.session import get_db
from app.db.base import Base

# Use a separate test database URL if configured, or default to a test database name
TEST_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI.replace(
    f"/{settings.POSTGRES_DB}", f"/test_{settings.POSTGRES_DB}"
) if settings.SQLALCHEMY_DATABASE_URI else "sqlite+aiosqlite:///:memory:"

from sqlalchemy.pool import NullPool

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    future=True,
    connect_args={"ssl": False},
    poolclass=NullPool,
)

TestAsyncSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create a session-wide event loop for running async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


from sqlalchemy import text

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Create database tables before tests and drop them after all tests complete.
    For SQLite in-memory, this is required. For PostgreSQL, it ensures a clean run.
    """
    # Dynamically create PostgreSQL test database if connecting to postgres
    if settings.SQLALCHEMY_DATABASE_URI and "sqlite" not in settings.SQLALCHEMY_DATABASE_URI:
        admin_url = settings.SQLALCHEMY_DATABASE_URI.replace(f"/{settings.POSTGRES_DB}", "/postgres")
        admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT", connect_args={"ssl": False})
        try:
            async with admin_engine.connect() as conn:
                await conn.execute(text(f"CREATE DATABASE test_{settings.POSTGRES_DB}"))
        except Exception:
            # Database might already exist or creation failed, ignore and continue
            pass
        finally:
            await admin_engine.dispose()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception:
        pass


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture that yields an AsyncSession running inside a transaction.
    The transaction is automatically rolled back at the end of each test.
    """
    async with TestAsyncSessionLocal() as session:
        async with session.begin():  # Start transaction
            yield session
            await session.rollback()  # Rollback changes to keep tests isolated


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that returns an HTTPX AsyncClient for making requests to the FastAPI app.
    It overrides the main get_db dependency to inject the test transactional db session.
    """
    # Override dependency
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    
    # Use ASGITransport for testing inside the FastAPI app direct runtime
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        yield ac
        
    # Clear overrides after test finishes
    app.dependency_overrides.clear()

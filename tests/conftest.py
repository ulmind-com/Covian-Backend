import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.main import app
from app.core.config import settings
from app.db.session import get_db

# Use a separate test database name for MongoDB test runs
TEST_DB_NAME = "test_project_form_prem"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create a session-wide event loop for running async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Clean the test database before and after the test run.
    """
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    # Ensure fresh start by dropping test database
    await client.drop_database(TEST_DB_NAME)
    yield
    # Cleanup after entire test session
    await client.drop_database(TEST_DB_NAME)
    client.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Fixture that yields an AsyncIOMotorDatabase instance for testing.
    Automatically clears all collections after each test to keep test isolation.
    """
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[TEST_DB_NAME]
    yield db
    # Delete all documents in all collections to isolate tests
    for collection_name in await db.list_collection_names():
        await db[collection_name].delete_many({})
    client.close()


@pytest.fixture
async def client(db_session: AsyncIOMotorDatabase) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that returns an HTTPX AsyncClient for making requests to the FastAPI app.
    It overrides the main get_db dependency to inject the test database.
    """
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

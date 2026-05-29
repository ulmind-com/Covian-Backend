from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

# Create the motor client globally to reuse connection pooling
client = AsyncIOMotorClient(settings.MONGODB_URL)

async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Dependency generator for MongoDB database.
    Yields the database instance.
    """
    db = client[settings.MONGODB_DB_NAME]
    try:
        yield db
    finally:
        pass

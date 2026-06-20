import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.user import User

async def main():
    try:
        client = AsyncIOMotorClient("mongodb://localhost:27017", serverSelectionTimeoutMS=100)
        await init_beanie(database=client.db_name, document_models=[User])
        print("init_beanie succeeded")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())

import asyncio
from beanie import init_beanie, Document
from motor.motor_asyncio import AsyncIOMotorClient

class TestUser3(Document):
    email: str

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.db_name, document_models=[TestUser3])
    print("TestUser3.email after init:", TestUser3.email)

asyncio.run(main())

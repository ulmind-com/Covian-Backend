import asyncio
from app.db.mongo import init_db
from app.models.user import User

async def list_users():
    await init_db()
    users = await User.find_all().to_list()
    for u in users:
        print(f"Role: {u.role}, Email: {u.email}")

asyncio.run(list_users())

import asyncio
from app.db.mongo import init_db
from app.models.user import User

async def test():
    await init_db()
    user_id_str = "6a1c17d206c7c76f03de6672" # Extracted from the sub in the token
    print(f"Testing User.get({user_id_str})...")
    try:
        user = await User.get(user_id_str)
        print("Found:", user.email if user else None)
    except Exception as e:
        print("Exception:", type(e), e)

if __name__ == "__main__":
    asyncio.run(test())

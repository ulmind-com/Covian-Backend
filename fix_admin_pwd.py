import asyncio
from app.core.security import get_password_hash
from app.db.mongo import init_db
from app.models.user import User

async def reset():
    await init_db()
    admin_email = "admin@corevita.co"
    user = await User.find_one(User.email == admin_email)
    if user:
        user.hashed_password = get_password_hash("adminpassword123")
        await user.save()
        print("Password reset successfully for", admin_email)
    else:
        print("User not found!")

asyncio.run(reset())

import asyncio
from app.core.security import get_password_hash
from app.db.mongo import init_db
from app.models.user import User

async def reset():
    await init_db()
    admin_email = "admin@corevita.com"
    user = await User.find_one(User.email == admin_email)
    if user:
        user.hashed_password = get_password_hash("adminpassword123")
        await user.save()
        print("Password reset successfully for", admin_email)
    else:
        new_admin = User(
            name="Super Admin",
            email=admin_email,
            hashed_password=get_password_hash("adminpassword123"),
            role="SUPER_ADMIN",
            is_active=True,
            is_verified=True
        )
        await new_admin.insert()
        print("Admin user created successfully:", admin_email)

asyncio.run(reset())

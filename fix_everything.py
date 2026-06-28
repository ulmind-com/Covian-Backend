"""
End-to-end fix script:
1. Verify data exists in the new database
2. Reset password for ALL admin users (both admin@corevita.co and admin@corevita.com)
3. Ensure at least one working SUPER_ADMIN exists
"""
import asyncio
from app.core.security import get_password_hash
from app.db.mongo import init_db
from app.models.user import User

async def fix_all():
    await init_db()
    
    # 1. List all users in the database
    all_users = await User.find_all().to_list()
    print(f"\n=== Found {len(all_users)} users in the new database ===")
    for u in all_users:
        print(f"  - {u.email} | role: {u.role} | active: {u.is_active}")
    
    # 2. Reset password for admin@corevita.co
    admin1 = await User.find_one(User.email == "admin@corevita.co")
    if admin1:
        admin1.hashed_password = get_password_hash("adminpassword123")
        admin1.role = "SUPER_ADMIN"
        admin1.is_active = True
        admin1.is_verified = True
        await admin1.save()
        print(f"\n✅ Password reset for admin@corevita.co")
    else:
        print(f"\n❌ admin@corevita.co NOT found")
    
    # 3. Reset password for admin@corevita.com
    admin2 = await User.find_one(User.email == "admin@corevita.com")
    if admin2:
        admin2.hashed_password = get_password_hash("adminpassword123")
        admin2.role = "SUPER_ADMIN"
        admin2.is_active = True
        admin2.is_verified = True
        await admin2.save()
        print(f"✅ Password reset for admin@corevita.com")
    else:
        # Create admin@corevita.com if it doesn't exist
        new_admin = User(
            name="Super Admin",
            email="admin@corevita.com",
            hashed_password=get_password_hash("adminpassword123"),
            role="SUPER_ADMIN",
            is_active=True,
            is_verified=True,
        )
        await new_admin.insert()
        print(f"✅ Created admin@corevita.com (was missing)")

    # 4. Final verification
    print(f"\n=== Final User List ===")
    all_users = await User.find_all().to_list()
    for u in all_users:
        print(f"  - {u.email} | role: {u.role} | active: {u.is_active} | verified: {u.is_verified}")
    
    print(f"\n🎉 All fixes applied! You can now login with:")
    print(f"   Email: admin@corevita.com  OR  admin@corevita.co")
    print(f"   Password: adminpassword123")

asyncio.run(fix_all())

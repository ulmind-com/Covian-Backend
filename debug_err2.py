import asyncio
from datetime import datetime, timezone
from app.schemas.user import UserResponse

print("Attempting to instantiate UserResponse")
try:
    ur = UserResponse(
        id="123456789012345678901234",
        email="test@test.com",
        name="Test",
        role="CLIENT",
        is_active=True,
        is_verified=False,
        created_at=datetime.now(timezone.utc)
    )
    print(ur)
except Exception as e:
    import traceback
    traceback.print_exc()

import asyncio
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserCreate, UserResponse

print("Attempting to instantiate UserCreate")
try:
    uc = UserCreate(email="test@test.com", name="Test", password="password123")
    print(uc)
except Exception as e:
    import traceback
    traceback.print_exc()


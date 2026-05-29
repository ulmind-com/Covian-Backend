from datetime import datetime, timezone
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field, EmailStr

class User(Document):
    name: str
    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    role: str = "CLIENT"  # Default role matches role name: SUPER_ADMIN, ADMIN, RECRUITER, CLIENT
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Samiran Samanta",
                "email": "samiran@example.com",
                "role": "SUPER_ADMIN",
                "is_active": True,
                "created_at": "2026-05-29T19:54:47Z"
            }
        }

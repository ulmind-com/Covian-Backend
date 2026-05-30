from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, Indexed
from pydantic import Field, EmailStr


class User(Document):
    """
    Production-grade User document with full profile, RBAC, and tracking fields.
    Backward-compatible with all existing references to User.role (str).
    """
    name: str
    email: Indexed(EmailStr, unique=True)
    hashed_password: str

    # RBAC — role name string (e.g. "SUPER_ADMIN", "ADMIN", "RECRUITER", "CLIENT")
    role: Indexed(str) = "CLIENT"

    # Optional per-user permission overrides (augments or restricts role permissions)
    permissions: List[str] = Field(default_factory=list)

    # Profile fields
    avatar_url: Optional[str] = None
    phone: Optional[str] = None

    # Status flags (indexed via Settings.indexes, not Indexed() wrapper — bool not supported)
    is_active: bool = True
    is_verified: bool = False

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

    class Settings:
        name = "users"
        indexes = [
            "email",
            "role",
            "is_active",
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Prem Kumar",
                "email": "premjeet.dev26@gmail.com",
                "role": "SUPER_ADMIN",
                "is_active": True,
                "is_verified": True,
                "phone": "+919876543210",
                "avatar_url": "https://cdn.example.com/avatars/prem.jpg",
                "created_at": "2026-05-30T14:00:00Z"
            }
        }

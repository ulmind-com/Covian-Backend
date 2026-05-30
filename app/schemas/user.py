from datetime import datetime
from typing import Annotated, Any, List, Optional
from pydantic import BaseModel, EmailStr, Field, BeforeValidator

# ─── Custom BSON ObjectId → str serializer ───────────────────────────────────
ObjectIdStr = Annotated[str, BeforeValidator(lambda v: str(v) if v is not None else v)]


# ─── BASE ─────────────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Unique email address")
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field("CLIENT", description="SUPER_ADMIN | ADMIN | RECRUITER | CLIENT")
    is_active: bool = Field(True)


# ─── CREATE (Admin creates user) ──────────────────────────────────────────────
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100, description="Plain-text password")
    is_verified: bool = Field(False)
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    permissions: List[str] = Field(default_factory=list, description="Custom permission overrides")


# ─── ADMIN UPDATE (admin changes role/status/etc) ────────────────────────────
class AdminUserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    permissions: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None


# ─── SELF UPDATE (user updates their own profile) ────────────────────────────
class UserUpdate(BaseModel):
    """Legacy + profile-only update schema. Role cannot be elevated by self."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[str] = None        # ignored on /me endpoint
    is_active: Optional[bool] = None  # ignored on /me endpoint
    avatar_url: Optional[str] = None
    phone: Optional[str] = None


class ProfileUpdate(BaseModel):
    """Strict self-profile update — only personal fields."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = None
    phone: Optional[str] = None


# ─── PASSWORD ─────────────────────────────────────────────────────────────────
class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ─── RESPONSE ─────────────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    id: ObjectIdStr
    email: EmailStr
    name: str
    role: str
    is_active: bool
    is_verified: bool = False
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    permissions: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── ADMIN ANALYTICS ──────────────────────────────────────────────────────────
class UsersByRole(BaseModel):
    role: str
    count: int


class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    verified_users: int
    users_by_role: List[UsersByRole]
    new_users_last_7_days: int


# ─── JWT TOKENS ───────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    type: str
    exp: datetime

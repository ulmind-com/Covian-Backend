from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="The unique email address of the user")
    name: str = Field(..., min_length=1, max_length=100, description="The name of the user")
    role: str = Field("CLIENT", description="User role (SUPER_ADMIN, ADMIN, RECRUITER, CLIENT)")
    is_active: bool = Field(True, description="Whether the user account is active")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100, description="User password (min 8 characters)")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="New email address")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="New name")
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="New password")
    role: Optional[str] = Field(None, description="New role")
    is_active: Optional[bool] = Field(None, description="Update active status")

from typing import Annotated, Any
from pydantic import BeforeValidator

# Custom validator to convert BSON ObjectId/PydanticObjectId to string during serialization
ObjectIdStr = Annotated[str, BeforeValidator(lambda v: str(v) if v is not None else v)]

class UserResponse(UserBase):
    id: ObjectIdStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    type: str
    exp: datetime

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_db
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.user_service import user_service

router = APIRouter()


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="The refresh token returned during login")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Any:
    """
    Register a new user in the system.
    """
    user = await user_service.register(db, user_in=user_in)
    return user


@router.post("/login", response_model=Token)
async def login(
    db: AsyncIOMotorDatabase = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, retrieve access and refresh tokens.
    Expects standard application/x-www-form-urlencoded format with 'username' and 'password' fields.
    Note: 'username' should be the user's email address.
    """
    user = await user_service.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
        
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Any:
    """
    Receive a valid refresh token and obtain a new set of access & refresh tokens.
    """
    # Verify the refresh token and get user ID
    user_id_str = verify_token(request.refresh_token, is_refresh=True)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
        
    try:
        import uuid
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        )
        
    user = await user_service.get_by_id(db, user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
        
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }

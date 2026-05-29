from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_active_user, RoleChecker, PermissionChecker
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.services.user_service import user_service
from app.repositories.user_repo import user_repo

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get profile information of the currently authenticated active user.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update profile details for the currently logged in user.
    """
    # Prevent regular users from elevating their own roles
    if user_in.role and user_in.role != current_user.role:
        user_in.role = current_user.role

    updated_user = await user_service.update(db_user=current_user, user_in=user_in)
    return updated_user


# ==============================================================================
# ADMIN OPERATIONS
# ==============================================================================

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """
    List all platform users with pagination.
    Accessible only to SUPER_ADMIN and ADMIN.
    """
    return await user_repo.get_multi(skip=skip, limit=limit)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_by_admin(
    user_in: UserCreate,
    current_user: User = Depends(PermissionChecker("manage_users"))
) -> Any:
    """
    Admin registers a new user with any specified platform role.
    Requires 'manage_users' permission.
    """
    user = await user_service.register(user_in=user_in)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """
    Fetch details of a user by their MongoDB ID.
    Accessible only to SUPER_ADMIN and ADMIN.
    """
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_admin(
    user_id: str,
    user_in: UserUpdate,
    current_user: User = Depends(PermissionChecker("manage_users"))
) -> Any:
    """
    Update a specific user profile and status (e.g. change role, activate/deactivate).
    Requires 'manage_users' permission.
    """
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    updated_user = await user_service.update(db_user=user, user_in=user_in)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_admin(
    user_id: str,
    current_user: User = Depends(PermissionChecker("manage_users"))
) -> Any:
    """
    Delete a user from the platform permanently.
    Requires 'manage_users' permission.
    """
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    await user.delete()
    return None

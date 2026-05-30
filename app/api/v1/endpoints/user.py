"""
User Management Endpoints
==========================
Complete admin-controlled user management system.

Routes:
  GET    /users/me                      Self profile
  PUT    /users/me                      Update self profile
  POST   /users/me/change-password      Change own password
  POST   /users/forgot-password         Request password reset email
  POST   /users/reset-password          Apply reset token + new password
  GET    /users/                         Admin: list users (paginated, filtered)
  POST   /users/                         Admin: create user
  GET    /users/stats                   Admin: user analytics
  GET    /users/{id}                    Admin: get user by ID
  PUT    /users/{id}                    Admin: update user
  DELETE /users/{id}                    Admin: soft-delete user
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.api.deps import get_current_active_user, PermissionChecker, RoleChecker
from app.models.user import User
from app.schemas.user import (
    AdminUserUpdate,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ProfileUpdate,
    ResetPasswordRequest,
    UserCreate,
    UserResponse,
    UserStatsResponse,
    UserUpdate,
)
from app.services.user_service import user_service
from app.utils.audit import log_action

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# SELF PROFILE (any authenticated user)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/me", response_model=UserResponse, summary="Get my profile")
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Return the profile of the currently authenticated user."""
    return current_user


@router.put("/me", response_model=UserResponse, summary="Update my profile")
async def update_my_profile(
    profile_in: ProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update personal profile fields (name, avatar_url, phone).
    Role and is_active cannot be changed through this endpoint.
    """
    updated = await user_service.update_profile(
        db_user=current_user, profile_in=profile_in
    )
    await log_action(
        action="UPDATE_PROFILE",
        details=f"User {current_user.email} updated their own profile",
        user=current_user,
        request=request,
    )
    return updated


# ══════════════════════════════════════════════════════════════════════════════
# PASSWORD MANAGEMENT (any authenticated user)
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/me/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change my password",
)
async def change_my_password(
    request_in: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Authenticated user changes their own password.
    Requires the current password for verification.
    """
    await user_service.change_password(user=current_user, request=request_in)
    await log_action(
        action="PASSWORD_CHANGED",
        details=f"User {current_user.email} changed their password",
        user=current_user,
        request=request,
    )
    return {"message": "Password updated successfully."}


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset email",
)
async def forgot_password(request_in: ForgotPasswordRequest) -> dict:
    """
    Sends a password reset token email.
    Always returns 200 to prevent email enumeration.
    """
    await user_service.request_password_reset(email=str(request_in.email))
    return {
        "message": "If an account with that email exists, a reset link has been sent."
    }


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Apply reset token and set new password",
)
async def reset_password(request_in: ResetPasswordRequest) -> dict:
    """Apply a one-time password reset token and set the new password."""
    await user_service.reset_password(
        token=request_in.token, new_password=request_in.new_password
    )
    return {"message": "Password reset successfully. You can now log in."}


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN: USER ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/stats",
    response_model=UserStatsResponse,
    summary="[Admin] User analytics and statistics",
)
async def get_user_stats(
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """
    Admin dashboard analytics:
    - Total, active, inactive users
    - Users by role
    - New signups in the last 7 days
    - Verified users count
    """
    return await user_service.get_user_stats()


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN: USER CRUD
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/",
    response_model=List[UserResponse],
    summary="[Admin] List all users with filters",
)
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=500),
    role: Optional[str] = Query(default=None, description="Filter by role name"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    search: Optional[str] = Query(default=None, description="Search by name or email"),
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """
    Paginated, searchable user list.
    Supports filters: role, is_active, search (name/email substring).
    """
    return await user_service.list_users(
        skip=skip, limit=limit, role=role, is_active=is_active, search=search
    )


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create a new user",
)
async def admin_create_user(
    user_in: UserCreate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_users")),
) -> Any:
    """
    Admin creates a user with a specified role.
    - Cannot create SUPER_ADMIN unless actor is SUPER_ADMIN
    - Sends welcome email to the new user
    - Requires 'manage_users' permission
    """
    new_user = await user_service.admin_create_user(user_in=user_in, admin=current_user)
    await log_action(
        action="ADMIN_CREATE_USER",
        details=f"Admin {current_user.email} created user {new_user.email} (role: {new_user.role})",
        user=current_user,
        request=request,
    )
    return new_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="[Admin] Get user by ID",
)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Fetch full user details by MongoDB document ID."""
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="[Admin] Update user profile, role, or status",
)
async def admin_update_user(
    user_id: str,
    user_in: AdminUserUpdate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_users")),
) -> Any:
    """
    Admin updates any user field.
    Guards:
    - Cannot change your own role
    - Cannot modify another SUPER_ADMIN unless you are SUPER_ADMIN
    Logs audit event for role changes.
    """
    target = await user_service.get_by_id(user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    updated = await user_service.admin_update_user(
        target_user=target, user_in=user_in, admin=current_user
    )
    await log_action(
        action="ADMIN_UPDATE_USER",
        details=f"Admin {current_user.email} updated user {target.email}",
        user=current_user,
        request=request,
    )
    return updated


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="[Admin] Soft-delete (deactivate) a user",
)
async def soft_delete_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_users")),
) -> dict:
    """
    Soft-delete a user by setting is_active = False.
    The user's data is preserved; they cannot log in.
    Cannot deactivate the last active SUPER_ADMIN.
    """
    target = await user_service.get_by_id(user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await user_service.soft_delete_user(target_user=target, admin=current_user)
    await log_action(
        action="ADMIN_DEACTIVATE_USER",
        details=f"Admin {current_user.email} deactivated user {target.email}",
        user=current_user,
        request=request,
    )
    return {
        "message": f"User '{target.email}' has been deactivated.",
        "user_id": str(target.id),
    }

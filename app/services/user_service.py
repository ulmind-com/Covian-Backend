"""
User Service
=============
Business logic layer for all User operations.
Architecture: API → Service → Repository → DB

Handles: registration, authentication, password management,
         admin CRUD, profile updates, and analytics.
"""
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException, status

from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.role import Role
from app.repositories.user_repo import user_repo
from app.schemas.user import (
    AdminUserUpdate,
    ChangePasswordRequest,
    ProfileUpdate,
    UserCreate,
    UserStatsResponse,
    UsersByRole,
    UserUpdate,
)

logger = logging.getLogger("app.user_service")

# In-memory store for password reset tokens (use Redis in production)
_reset_tokens: Dict[str, tuple] = {}  # token → (user_id, expiry)


class UserService:
    """
    Orchestrates all user-related business logic.
    Delegates raw DB calls to UserRepository.
    """

    # ── Registration & Authentication ─────────────────────────────────────────

    async def register(self, *, user_in: UserCreate) -> User:
        """
        Register a new user after email uniqueness check.
        Sends welcome email via background worker.
        """
        existing_user = await user_repo.get_by_email(email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address is already registered.",
            )

        hashed_password = get_password_hash(user_in.password)
        db_user = await user_repo.create(user_in=user_in, hashed_password=hashed_password)

        # Enqueue welcome email in background (non-blocking)
        try:
            from app.utils.background import enqueue_email_notification
            await enqueue_email_notification(
                recipient_email=str(db_user.email),
                title="Welcome to CoreVita Advisory!",
                message=(
                    f"Hello {db_user.name},\n\n"
                    "Your account has been created successfully on the CoreVita platform.\n"
                    "You can now log in and start using the system.\n\n"
                    "— CoreVita Team"
                ),
            )
        except Exception as e:
            logger.warning(f"[UserService] Welcome email failed for {db_user.email}: {e}")

        # Log activity
        try:
            from app.utils.activity import log_activity
            await log_activity(
                event_type="USER_REGISTERED",
                entity_type="user",
                entity_id=str(db_user.id),
                title=f"New user registered: {db_user.name}",
                description=f"User {db_user.email} registered with role {db_user.role}.",
            )
        except Exception as e:
            logger.warning(f"[UserService] Activity log failed: {e}")

        return db_user

    async def authenticate(self, *, email: str, password: str) -> Optional[User]:
        """
        Verify email + password. Stamps last_login on success.
        Returns None on failure (caller raises appropriate HTTP error).
        """
        user = await user_repo.get_by_email(email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None

        # Stamp last login timestamp
        await user_repo.update_last_login(user)

        # Log login activity
        try:
            from app.utils.activity import log_activity
            await log_activity(
                event_type="USER_LOGIN",
                entity_type="user",
                entity_id=str(user.id),
                title=f"User logged in: {user.name}",
                description=f"Successful login for {user.email}.",
            )
        except Exception:
            pass

        return user

    # ── Getters ───────────────────────────────────────────────────────────────

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by MongoDB ID string."""
        return await user_repo.get_by_id(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email address."""
        return await user_repo.get_by_email(email)

    async def list_users(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[User]:
        """Paginated + filtered user listing."""
        return await user_repo.get_multi(
            skip=skip, limit=limit, role=role, is_active=is_active, search=search
        )

    # ── Admin CRUD ────────────────────────────────────────────────────────────

    async def admin_create_user(
        self,
        *,
        user_in: UserCreate,
        admin: User,
    ) -> User:
        """
        Admin creates a user with any role. Logs audit event.
        Cannot create a SUPER_ADMIN unless the actor is SUPER_ADMIN.
        """
        if user_in.role == "SUPER_ADMIN" and admin.role != "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only SUPER_ADMIN can create another SUPER_ADMIN account.",
            )
        db_user = await self.register(user_in=user_in)

        # Audit
        try:
            from app.utils.audit import log_action
            from fastapi import Request
            await log_action(
                action="ADMIN_CREATE_USER",
                details=f"Admin {admin.email} created user {db_user.email} with role {db_user.role}",
                user=admin,
            )
        except Exception:
            pass

        return db_user

    async def admin_update_user(
        self,
        *,
        target_user: User,
        user_in: AdminUserUpdate,
        admin: User,
    ) -> User:
        """
        Admin updates any user field including role.
        Enforces: cannot downgrade own role, cannot demote SUPER_ADMIN.
        """
        # Prevent self role downgrade
        if str(target_user.id) == str(admin.id) and user_in.role and user_in.role != admin.role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role.",
            )

        # Only SUPER_ADMIN can touch SUPER_ADMIN users
        if target_user.role == "SUPER_ADMIN" and admin.role != "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only SUPER_ADMIN can modify another SUPER_ADMIN account.",
            )

        updated = await user_repo.update(db_user=target_user, user_in=user_in)

        # Audit role change
        if user_in.role and user_in.role != target_user.role:
            try:
                from app.utils.audit import log_action
                await log_action(
                    action="ADMIN_ROLE_CHANGE",
                    details=f"Admin {admin.email} changed role of {target_user.email} to {user_in.role}",
                    user=admin,
                )
            except Exception:
                pass

        return updated

    async def soft_delete_user(
        self,
        *,
        target_user: User,
        admin: User,
    ) -> User:
        """
        Soft-delete: deactivate user (is_active = False).
        Cannot deactivate the last SUPER_ADMIN.
        """
        if target_user.role == "SUPER_ADMIN":
            count = await user_repo.count(query={"role": "SUPER_ADMIN", "is_active": True})
            if count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate the last active SUPER_ADMIN account.",
                )

        deactivated = await user_repo.soft_delete(target_user)

        try:
            from app.utils.audit import log_action
            await log_action(
                action="ADMIN_DEACTIVATE_USER",
                details=f"Admin {admin.email} deactivated user {target_user.email}",
                user=admin,
            )
            from app.utils.activity import log_activity
            await log_activity(
                event_type="USER_DEACTIVATED",
                entity_type="user",
                entity_id=str(target_user.id),
                title=f"User deactivated: {target_user.name}",
                description=f"User {target_user.email} was deactivated by {admin.email}.",
                actor=admin,
            )
        except Exception:
            pass

        return deactivated

    # ── Self Profile Update ────────────────────────────────────────────────────

    async def update_profile(self, *, db_user: User, profile_in: ProfileUpdate) -> User:
        """User updates their own personal profile (name, avatar, phone)."""
        update_data = profile_in.model_dump(exclude_unset=True)
        return await user_repo.update(db_user=db_user, user_in=update_data)

    async def update(self, *, db_user: User, user_in: UserUpdate) -> User:
        """Legacy update used by existing endpoints. Hashes password if provided."""
        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            db_user.hashed_password = get_password_hash(update_data.pop("password"))
        return await user_repo.update(db_user=db_user, user_in=update_data)

    # ── Password Management ────────────────────────────────────────────────────

    async def change_password(
        self,
        *,
        user: User,
        request: ChangePasswordRequest,
    ) -> None:
        """
        User changes their own password after verifying the current one.
        """
        if not verify_password(request.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )
        user.hashed_password = get_password_hash(request.new_password)
        user.updated_at = datetime.now(timezone.utc)
        await user.save()

        try:
            from app.utils.audit import log_action
            await log_action(
                action="PASSWORD_CHANGED",
                details=f"User {user.email} changed their password",
                user=user,
            )
        except Exception:
            pass

    async def request_password_reset(self, *, email: str) -> None:
        """
        Generate a secure reset token and send it via email.
        Always returns 200 (to not reveal user existence).
        """
        user = await user_repo.get_by_email(email)
        if not user:
            logger.info(f"[PasswordReset] No user found for {email}, skipping silently.")
            return

        token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        _reset_tokens[token] = (str(user.id), expiry)

        try:
            from app.utils.background import enqueue_email_notification
            await enqueue_email_notification(
                recipient_email=str(user.email),
                title="Password Reset Request — CoreVita",
                message=(
                    f"Hello {user.name},\n\n"
                    f"You requested a password reset.\n"
                    f"Your reset token is:\n\n  {token}\n\n"
                    f"This token expires in 1 hour. Do not share it.\n\n"
                    f"If you did not request this, please ignore this email.\n\n"
                    f"— CoreVita Security Team"
                ),
            )
        except Exception as e:
            logger.warning(f"[PasswordReset] Email failed for {email}: {e}")

    async def reset_password(self, *, token: str, new_password: str) -> None:
        """
        Validate the reset token and apply the new hashed password.
        """
        entry = _reset_tokens.get(token)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )
        user_id, expiry = entry
        if datetime.now(timezone.utc) > expiry:
            del _reset_tokens[token]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired. Please request a new one.",
            )

        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account no longer exists.",
            )

        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.now(timezone.utc)
        await user.save()
        del _reset_tokens[token]

        try:
            from app.utils.audit import log_action
            await log_action(
                action="PASSWORD_RESET",
                details=f"Password reset completed for user {user.email}",
                user=user,
            )
        except Exception:
            pass

    # ── Analytics ─────────────────────────────────────────────────────────────

    async def get_user_stats(self) -> UserStatsResponse:
        """
        Aggregate user statistics for the admin dashboard.
        """
        from datetime import timedelta
        total = await user_repo.count()
        active = await user_repo.count(query={"is_active": True})
        inactive = await user_repo.count(query={"is_active": False})
        verified = await user_repo.count(query={"is_verified": True})

        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        new_users = await user_repo.count(
            query={"created_at": {"$gte": seven_days_ago}}
        )

        # Per-role count via aggregation
        pipeline = [
            {"$group": {"_id": "$role", "count": {"$sum": 1}}}
        ]
        role_agg = await User.aggregate(pipeline).to_list()
        users_by_role = [
            UsersByRole(role=item["_id"], count=item["count"])
            for item in role_agg
        ]

        return UserStatsResponse(
            total_users=total,
            active_users=active,
            inactive_users=inactive,
            verified_users=verified,
            users_by_role=users_by_role,
            new_users_last_7_days=new_users,
        )

    # ── RBAC helpers ──────────────────────────────────────────────────────────

    async def get_effective_permissions(self, user: User) -> List[str]:
        """
        Resolve the effective permission set for a user:
        1. SUPER_ADMIN → ["*"] (wildcard)
        2. Role permissions from the roles collection
        3. Merged with user-level permission overrides
        """
        if user.role == "SUPER_ADMIN":
            return ["*"]

        role = await Role.find_one(Role.name == user.role)
        role_perms: List[str] = role.permissions if role else []

        # Merge without duplicates
        merged = list(set(role_perms + user.permissions))
        return merged


user_service = UserService()

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.security import verify_token
from app.models.user import User
from app.models.role import Role

# OAuth2 scheme configures token retrieval
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Validates token and returns the current Beanie User document.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id_str = verify_token(token, is_refresh=False)
    if not user_id_str:
        raise credentials_exception
        
    user = await User.get(user_id_str)
    if not user:
        raise credentials_exception
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Guards that the authenticated user is currently active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated"
        )
    return current_user


class RoleChecker:
    """
    Dependency to restrict endpoint access to specific roles.
    Example: Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
    """
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return current_user


class PermissionChecker:
    """
    Dependency to check if the user's role has a required granular permission.
    Example: Depends(PermissionChecker("manage_users"))
    """
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        # SUPER_ADMIN bypasses all permission checks
        if current_user.role == "SUPER_ADMIN":
            return current_user

        role = await Role.find_one(Role.name == current_user.role)
        if not role or self.required_permission not in role.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {self.required_permission}"
            )
        return current_user

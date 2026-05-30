"""
User Repository
================
All raw MongoDB/Beanie queries for the User model.
Architecture: API → Service → Repository → DB
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    """
    Database query repository for the User model using Beanie ODM.
    Handles all raw DB operations; business logic lives in UserService.
    """

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Fetch a user by their unique MongoDB string ID."""
        return await User.get(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch a user by their unique email address."""
        return await User.find_one(User.email == email)

    async def create(self, *, user_in: UserCreate, hashed_password: str) -> User:
        """Insert a new User document into MongoDB."""
        db_user = User(
            email=user_in.email,
            name=user_in.name,
            hashed_password=hashed_password,
            role=user_in.role,
            is_active=user_in.is_active,
            is_verified=getattr(user_in, "is_verified", False),
            avatar_url=getattr(user_in, "avatar_url", None),
            phone=getattr(user_in, "phone", None),
            permissions=getattr(user_in, "permissions", []),
        )
        await db_user.insert()
        return db_user

    async def update(self, *, db_user: User, user_in: Any) -> User:
        """Apply an update dict or schema to an existing User document."""
        if isinstance(user_in, dict):
            update_data = user_in
        else:
            update_data = user_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            # Skip raw password — hashing is done at service layer
            if field == "password":
                continue
            setattr(db_user, field, value)

        db_user.updated_at = datetime.now(timezone.utc)
        await db_user.save()
        return db_user

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[User]:
        """
        Paginated user list with optional filters:
          - role: exact role name match
          - is_active: bool filter
          - search: substring match on name or email
        """
        query: Dict[str, Any] = {}

        if role:
            query["role"] = role
        if is_active is not None:
            query["is_active"] = is_active

        if search:
            import re
            pattern = re.compile(search, re.IGNORECASE)
            query["$or"] = [
                {"name": {"$regex": pattern}},
                {"email": {"$regex": pattern}},
            ]

        return await User.find(query).skip(skip).limit(limit).to_list()

    async def count(self, *, query: Optional[Dict] = None) -> int:
        """Count users matching an optional filter dict."""
        if query:
            return await User.find(query).count()
        return await User.count()

    async def update_last_login(self, user: User) -> None:
        """Stamp last_login timestamp without a full document reload."""
        user.last_login = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        await user.save()

    async def soft_delete(self, user: User) -> User:
        """Deactivate user without physical deletion (is_active = False)."""
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        await user.save()
        return user


user_repo = UserRepository()

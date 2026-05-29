from typing import Optional, List
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class UserRepository:
    """
    Database query repository for the User model using Beanie ODM.
    """

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Fetch a user by their unique string ID.
        """
        return await User.get(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Fetch a user by their email address.
        """
        return await User.find_one(User.email == email)

    async def create(self, *, user_in: UserCreate, hashed_password: str) -> User:
        """
        Create a new user document in the database.
        """
        db_user = User(
            email=user_in.email,
            name=user_in.name,
            hashed_password=hashed_password,
            role=user_in.role,
            is_active=user_in.is_active,
        )
        await db_user.insert()
        return db_user

    async def update(self, *, db_user: User, user_in: UserUpdate | dict) -> User:
        """
        Update an existing user document.
        """
        if isinstance(user_in, dict):
            update_data = user_in
        else:
            update_data = user_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "password" and value is not None:
                continue
            setattr(db_user, field, value)

        await db_user.save()
        return db_user

    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Retrieve list of users with pagination.
        """
        return await User.find_all().skip(skip).limit(limit).to_list()

user_repo = UserRepository()

import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """
    Database query repository for the User model.
    Handles CRUD operations directly using SQLAlchemy async sessions.
    """

    async def get_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """
        Fetch a user by their unique UUID.
        """
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Fetch a user by their email address.
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, user_in: UserCreate, hashed_password: str) -> User:
        """
        Create a new user record in the database.
        """
        db_user = User(
            email=user_in.email,
            name=user_in.name,
            hashed_password=hashed_password,
            is_active=user_in.is_active,
        )
        db.add(db_user)
        await db.flush()  # Populates user.id without committing the entire transaction yet
        return db_user

    async def update(
        self, db: AsyncSession, *, db_user: User, user_in: UserUpdate | dict
    ) -> User:
        """
        Update an existing user record.
        """
        if isinstance(user_in, dict):
            update_data = user_in
        else:
            update_data = user_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "password" and value is not None:
                # Password hashing is handled at the service layer;
                # the repository expects hashed_password if updating password
                continue
            setattr(db_user, field, value)

        db.add(db_user)
        await db.flush()
        return db_user


# Instantiate user repository to be imported elsewhere
user_repo = UserRepository()

import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash, verify_password
from app.db.models.user import User
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """
    Business logic layer for User actions.
    Combines security operations with the database repository.
    """

    async def register(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        """
        Register a new user after verifying that the email is unique.
        """
        existing_user = await user_repo.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address is already registered.",
            )

        hashed_password = get_password_hash(user_in.password)
        db_user = await user_repo.create(
            db, user_in=user_in, hashed_password=hashed_password
        )
        return db_user

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Optional[User]:
        """
        Authenticate a user by email and password.
        Returns the User object if authentication is successful, otherwise None.
        """
        user = await user_repo.get_by_email(db, email=email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
            
        return user

    async def get_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieve a user record by ID.
        """
        return await user_repo.get_by_id(db, user_id)

    async def update(
        self, db: AsyncSession, *, db_user: User, user_in: UserUpdate
    ) -> User:
        """
        Update user details and hash the new password if one is provided.
        """
        update_data = user_in.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            db_user.hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]

        return await user_repo.update(db, db_user=db_user, user_in=update_data)


# Instantiate user service to be imported elsewhere
user_service = UserService()

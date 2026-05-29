from typing import Optional, List
from fastapi import HTTPException, status
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate, UserUpdate

class UserService:
    """
    Business logic layer for User actions.
    Combines security operations with the Beanie database repository.
    """

    async def register(self, *, user_in: UserCreate) -> User:
        """
        Register a new user after verifying that the email is unique.
        """
        existing_user = await user_repo.get_by_email(email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address is already registered.",
            )

        hashed_password = get_password_hash(user_in.password)
        db_user = await user_repo.create(
            user_in=user_in, hashed_password=hashed_password
        )
        return db_user

    async def authenticate(self, *, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.
        Returns the User object if authentication is successful, otherwise None.
        """
        user = await user_repo.get_by_email(email=email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
            
        return user

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user record by ID.
        """
        return await user_repo.get_by_id(user_id)

    async def update(self, *, db_user: User, user_in: UserUpdate) -> User:
        """
        Update user details and hash the new password if one is provided.
        """
        update_data = user_in.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            db_user.hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]

        return await user_repo.update(db_user=db_user, user_in=update_data)

user_service = UserService()

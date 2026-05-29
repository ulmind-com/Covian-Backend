import uuid
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """
    Database query repository for the User model.
    Handles CRUD operations directly using Motor async connections.
    """

    async def get_by_id(self, db: AsyncIOMotorDatabase, user_id: uuid.UUID) -> Optional[User]:
        """
        Fetch a user by their unique UUID.
        """
        user_dict = await db["users"].find_one({"id": str(user_id)})
        if user_dict:
            return User(**user_dict)
        return None

    async def get_by_email(self, db: AsyncIOMotorDatabase, email: str) -> Optional[User]:
        """
        Fetch a user by their email address.
        """
        user_dict = await db["users"].find_one({"email": email})
        if user_dict:
            return User(**user_dict)
        return None

    async def create(self, db: AsyncIOMotorDatabase, *, user_in: UserCreate, hashed_password: str) -> User:
        """
        Create a new user record in the database.
        """
        db_user = User(
            email=user_in.email,
            name=user_in.name,
            hashed_password=hashed_password,
            is_active=user_in.is_active,
        )
        user_dict = db_user.model_dump()
        user_dict["id"] = str(db_user.id)  # Store UUID as standard string
        
        await db["users"].insert_one(user_dict)
        return db_user

    async def update(
        self, db: AsyncIOMotorDatabase, *, db_user: User, user_in: UserUpdate | dict
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
                continue
            setattr(db_user, field, value)

        user_dict = db_user.model_dump()
        user_dict["id"] = str(db_user.id)
        
        await db["users"].replace_one({"id": str(db_user.id)}, user_dict)
        return db_user


# Instantiate user repository to be imported elsewhere
user_repo = UserRepository()

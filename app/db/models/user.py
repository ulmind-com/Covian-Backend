import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class User(BaseModel):
    """
    User model representing a user document in MongoDB.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "name": "Jane Doe",
                "is_active": True,
                "created_at": "2026-05-29T19:49:18Z"
            }
        }

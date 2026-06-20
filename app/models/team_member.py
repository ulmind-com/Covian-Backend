from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field


class TeamMember(Document):
    """Core team member profile managed from admin CMS."""
    name: str
    designation: str
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "team_members"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Priya Sharma",
                "designation": "Chief HR Advisor",
                "bio": "Over 15 years of experience in strategic HR consulting.",
                "photo_url": "https://images.unsplash.com/photo-xyz",
                "email": "priya@covian.com",
                "linkedin_url": "https://linkedin.com/in/priya-sharma",
                "twitter_url": None,
                "display_order": 1,
                "is_active": True
            }
        }

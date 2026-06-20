from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field


class Testimonial(Document):
    """Client testimonial managed from admin CMS."""
    client_name: str
    client_designation: Optional[str] = None
    client_company: Optional[str] = None
    client_photo_url: Optional[str] = None
    content: str
    rating: int = Field(default=5, ge=1, le=5)
    is_featured: bool = False
    is_active: bool = True
    display_order: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "testimonials"

    class Config:
        json_schema_extra = {
            "example": {
                "client_name": "Rajesh Kumar",
                "client_designation": "CEO",
                "client_company": "TechCorp India",
                "client_photo_url": "https://images.unsplash.com/photo-xyz",
                "content": "CoreVita helped us build an exceptional team in record time.",
                "rating": 5,
                "is_featured": True,
                "is_active": True,
                "display_order": 1
            }
        }

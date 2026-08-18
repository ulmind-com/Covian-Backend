from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field


class GalleryPhoto(Document):
    """Photo for the website accordion gallery, managed from admin CMS."""
    image_url: str
    label: str
    description: Optional[str] = ""
    link: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "gallery_photos"

    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/gallery/photo1.jpg",
                "label": "Office Event",
                "description": "Annual company gathering 2025",
                "link": None,
                "display_order": 1,
                "is_active": True
            }
        }

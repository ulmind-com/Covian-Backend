from datetime import datetime, timezone
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field

class CMSPage(Document):
    slug: Indexed(str, unique=True)
    title: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "cms_pages"

    class Config:
        json_schema_extra = {
            "example": {
                "slug": "about-us",
                "title": "About CoreVita Advisory",
                "content": "CoreVita provides premium consulting and strategic advising.",
                "created_at": "2026-05-29T19:54:47Z"
            }
        }


class CMSBlog(Document):
    slug: Indexed(str, unique=True)
    title: str
    content: str
    author: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "cms_blogs"

    class Config:
        json_schema_extra = {
            "example": {
                "slug": "future-of-workforce",
                "title": "The Future of Consulting Workforces",
                "content": "A deep-dive analysis on how workforce strategies are evolving...",
                "author": "Chief Advisor",
                "created_at": "2026-05-29T19:54:47Z"
            }
        }


class CMSService(Document):
    name: str
    description: str
    price: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "cms_services"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Financial Restructuring Program",
                "description": "Comprehensive corporate financial re-engineering and liquidity analysis.",
                "price": 15000.00,
                "created_at": "2026-05-29T19:54:47Z"
            }
        }

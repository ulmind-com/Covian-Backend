from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, Indexed
from pydantic import Field


class News(Document):
    """Rich news/blog article with CMS controls."""
    slug: Indexed(str, unique=True)
    title: str
    content: str
    excerpt: Optional[str] = None
    author: str = "CoreVita Admin"
    featured_image_url: Optional[str] = None
    category: Optional[str] = None          # e.g. "Industry News", "Company Update"
    tags: List[str] = Field(default_factory=list)
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_published: bool = False
    is_featured: bool = False
    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "news"

    class Config:
        json_schema_extra = {
            "example": {
                "slug": "future-of-hr-consulting",
                "title": "The Future of HR Consulting in India",
                "content": "Full article content here...",
                "excerpt": "A brief summary of the article.",
                "author": "CoreVita Team",
                "featured_image_url": "https://images.unsplash.com/photo-xyz",
                "category": "Industry Insights",
                "tags": ["HR", "Consulting", "India"],
                "seo_title": "Future of HR Consulting — CoreVita Advisory",
                "seo_description": "Explore how HR consulting is transforming in India.",
                "is_published": True,
                "is_featured": False
            }
        }

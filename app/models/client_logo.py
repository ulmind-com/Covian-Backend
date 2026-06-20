from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field


class ClientLogo(Document):
    """Client/partner logo managed from admin CMS."""
    name: str
    logo_url: str
    website_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "client_logos"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Infosys",
                "logo_url": "https://example.com/logos/infosys.png",
                "website_url": "https://infosys.com",
                "display_order": 1,
                "is_active": True
            }
        }

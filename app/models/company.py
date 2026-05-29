from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, Indexed
from pydantic import Field

class Company(Document):
    name: Indexed(str)
    domain: str
    industry: str
    description: Optional[str] = None
    managers: List[str] = Field(default_factory=list)  # list of User emails or IDs
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "companies"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "CoreVita Advisory Private Limited",
                "domain": "corevita.in",
                "industry": "Consulting & Financial Advisory",
                "description": "Strategic advisory and business consulting firm.",
                "managers": ["manager@corevita.in"],
                "created_at": "2026-05-29T19:54:47Z"
            }
        }

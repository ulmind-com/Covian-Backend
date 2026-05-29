from datetime import datetime, timezone
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field, EmailStr

class Lead(Document):
    company_name: str
    contact_name: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    status: Indexed(str) = "NEW"  # NEW, CONTACTED, QUALIFIED, LOST
    assigned_to: Optional[str] = None  # Reference to User id (Recruiter/Admin)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "leads"

    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "ConsultCo Ltd",
                "contact_name": "Robert Dow",
                "contact_email": "robert@consultco.com",
                "contact_phone": "+15550199",
                "status": "NEW",
                "assigned_to": "651a2345bc6789def0123457",
                "created_at": "2026-05-29T19:54:47Z"
            }
        }

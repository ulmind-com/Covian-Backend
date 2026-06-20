from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, Indexed
from pydantic import Field, EmailStr


class Enquiry(Document):
    """General contact/business enquiry from the public website."""
    name: str
    email: Indexed(EmailStr)
    phone: Optional[str] = None
    company: Optional[str] = None
    service_interest: Optional[str] = None   # e.g. "HR Consulting", "Recruitment"
    message: str
    status: str = "NEW"                       # NEW, REVIEWING, REPLIED, CLOSED
    admin_notes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "enquiries"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Aditya Bose",
                "email": "aditya@company.com",
                "phone": "+919876543210",
                "company": "Bose Enterprises",
                "service_interest": "HR Consulting",
                "message": "We are looking for a strategic HR partner.",
                "status": "NEW"
            }
        }

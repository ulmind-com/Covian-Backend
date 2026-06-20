from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, Indexed
from pydantic import Field, EmailStr


class CaregiverEnquiry(Document):
    """Caregiver/eldercare staffing enquiry from public website."""
    name: str
    email: Indexed(EmailStr)
    phone: Optional[str] = None
    location: Optional[str] = None           # City/State where caregiver is needed
    service_type: Optional[str] = None       # e.g. "Full-time", "Part-time", "Night Duty"
    care_recipient: Optional[str] = None     # e.g. "Elderly Parent", "Post-Surgery Patient"
    message: str
    status: str = "NEW"                      # NEW, REVIEWING, CONTACTED, FULFILLED, CLOSED
    admin_notes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "caregiver_enquiries"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sunita Devi",
                "email": "sunita@gmail.com",
                "phone": "+919876543210",
                "location": "Mumbai, Maharashtra",
                "service_type": "Full-time",
                "care_recipient": "Elderly Parent",
                "message": "Looking for a compassionate caregiver for my 78-year-old mother.",
                "status": "NEW"
            }
        }

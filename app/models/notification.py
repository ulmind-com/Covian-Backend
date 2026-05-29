from datetime import datetime, timezone
from beanie import Document, Indexed
from pydantic import Field, EmailStr

class Notification(Document):
    recipient_email: Indexed(EmailStr)
    title: str
    message: str
    status: Indexed(str) = "PENDING"  # PENDING, SENT, FAILED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notifications"

    class Config:
        json_schema_extra = {
            "example": {
                "recipient_email": "candidate@example.com",
                "title": "Application Screened",
                "message": "Your profile has been advanced to the Interviewing stage for Senior Advisor.",
                "status": "PENDING",
                "created_at": "2026-05-29T19:54:47Z"
            }
        }

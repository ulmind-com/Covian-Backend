from datetime import datetime, timezone
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field

class AuditLog(Document):
    user_id: Optional[str] = None  # Reference to acting User id (None if system-level)
    user_email: Optional[str] = None
    action: Indexed(str)  # e.g., CREATE_USER, DEACTIVATE_USER, UPDATE_CMS
    details: str
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "audit_logs"

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "651a2345bc6789def0123457",
                "user_email": "admin@corevita.in",
                "action": "CREATE_USER",
                "details": "Created new client user: client@example.com",
                "ip_address": "127.0.0.1",
                "created_at": "2026-05-29T19:54:47Z"
            }
        }

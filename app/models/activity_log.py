from datetime import datetime, timezone
from typing import Any, Optional
from beanie import Document, Indexed
from pydantic import Field


class ActivityLog(Document):
    """
    Stores real-time system-wide events (candidate stage changes, lead creation,
    invoice payments, etc.) for the admin activity feed.
    """
    event_type: Indexed(str)          # e.g. CANDIDATE_STAGE_CHANGED, LEAD_CREATED, INVOICE_PAID
    entity_type: str                   # e.g. 'candidate', 'lead', 'invoice'
    entity_id: Optional[str] = None    # ID of the affected document
    title: str                         # Human-readable event title
    description: str                   # Detailed event description
    actor_id: Optional[str] = None     # User who triggered the event
    actor_email: Optional[str] = None
    metadata: dict = Field(default_factory=dict)  # Extra structured data
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "activity_logs"
        indexes = ["event_type", "entity_type", "created_at"]

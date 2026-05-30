from datetime import datetime, timezone
from typing import Any, Dict, Optional
from beanie import Document, Indexed
from pydantic import Field


class CandidateTimeline(Document):
    """
    Tracks every action/event on a specific candidate's lifecycle:
    application submitted, stage moved, notes added, email sent, etc.
    """
    candidate_id: Indexed(str)      # Foreign key: Candidate._id
    event_type: str                  # e.g. APPLICATION_CREATED, STAGE_CHANGED, NOTE_ADDED, EMAIL_SENT
    title: str                       # Short human-readable title
    description: str                 # Detailed description of what happened
    actor_id: Optional[str] = None   # User who performed the action
    actor_email: Optional[str] = None
    related_job_id: Optional[str] = None
    related_application_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "candidate_timelines"
        indexes = ["candidate_id", "created_at"]

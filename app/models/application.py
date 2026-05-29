from datetime import datetime, timezone
from typing import List
from beanie import Document, Indexed
from pydantic import Field

class Application(Document):
    job_id: Indexed(str)
    candidate_id: Indexed(str)
    current_stage: str = "Applied"  # Matches one of the job's pipeline stages
    notes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "applications"

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "651a2345bc6789def0123456",
                "candidate_id": "651a2345bc6789def0123458",
                "current_stage": "Screened",
                "notes": ["Clear communicator", "Passed first round financial modeling test"],
                "created_at": "2026-05-29T19:54:47Z"
            }
        }

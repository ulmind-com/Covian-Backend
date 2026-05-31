from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, Indexed
from pydantic import Field

class Job(Document):
    title: str
    description: str
    company_id: Indexed(str)  # Reference to Company id
    recruiter_id: Optional[str] = None  # Reference to User id
    status: Indexed(str) = "OPEN"  # OPEN, CLOSED, DRAFT
    pipeline_stages: List[str] = Field(
        default_factory=lambda: ["Applied", "Screened", "Interviewing", "Offer", "Rejected", "Hired"]
    )
    salary_range: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    job_type: Optional[str] = Field(None, description="Full-time, Part-time, Contract")
    experience_level: Optional[str] = Field(None, description="Entry, Mid, Senior, Executive")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "jobs"

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Senior Financial Advisor",
                "description": "Provide strategic financial consulting services.",
                "company_id": "651a2345bc6789def0123456",
                "recruiter_id": "651a2345bc6789def0123457",
                "status": "OPEN",
                "pipeline_stages": ["Applied", "Screened", "Interviewing", "Offer", "Rejected", "Hired"],
                "salary_range": "$120,000 - $150,000",
                "created_at": "2026-05-29T19:54:47Z"
            }
        }

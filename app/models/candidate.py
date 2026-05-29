from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, Indexed
from pydantic import Field, EmailStr

class Candidate(Document):
    name: str
    email: Indexed(EmailStr, unique=True)
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)  # Indexed in Settings config block for rapid filtering
    cv_url: Optional[str] = None  # Store URL to external storage (S3/Cloudinary)
    status: Indexed(str) = "AVAILABLE"  # AVAILABLE, PLACED, INACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "candidates"
        # Create multikey index on array field `skills` for fast skill-based searches
        indexes = [
            "skills",
            "status",
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Miller",
                "email": "jane.miller@example.com",
                "phone": "+919876543210",
                "skills": ["Corporate Strategy", "M&A Advisory", "Financial Modeling"],
                "cv_url": "https://s3.amazonaws.com/corevita-cvs/jane_miller_cv.pdf",
                "status": "AVAILABLE",
                "created_at": "2026-05-29T19:54:47Z"
            }
        }

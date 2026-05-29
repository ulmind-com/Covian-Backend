from typing import List
from beanie import Document, Indexed
from pydantic import Field

class Role(Document):
    name: Indexed(str, unique=True)  # e.g., SUPER_ADMIN, ADMIN, RECRUITER, CLIENT
    permissions: List[str] = Field(default_factory=list)  # e.g. ["manage_users", "manage_jobs"]

    class Settings:
        name = "roles"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "ADMIN",
                "permissions": ["manage_users", "manage_jobs", "manage_candidates", "view_reports"]
            }
        }

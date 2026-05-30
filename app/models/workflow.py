from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from beanie import Document, Indexed
from pydantic import Field


class WorkflowRule(Document):
    """
    Represents an automation rule: IF condition THEN action.
    Admins define these rules; they are triggered on system events.

    Example:
      trigger_event = "CANDIDATE_STAGE_CHANGED"
      condition     = {"stage": "Offer"}
      action_type   = "SEND_EMAIL"
      action_config = {"template": "offer_congratulations", "recipient_field": "candidate_email"}
    """
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True

    # WHEN this event occurs
    trigger_event: Indexed(str)   # CANDIDATE_STAGE_CHANGED | NEW_LEAD | INVOICE_PAID | APPLICATION_CREATED

    # IF these conditions match (key-value pairs matched against event payload)
    conditions: Dict[str, Any] = Field(default_factory=dict)

    # THEN perform this action
    action_type: str              # SEND_EMAIL | CREATE_ACTIVITY_LOG | UPDATE_LEAD_SCORE | WEBHOOK
    action_config: Dict[str, Any] = Field(default_factory=dict)

    created_by: Optional[str] = None  # Admin user ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0

    class Settings:
        name = "workflows"
        indexes = ["trigger_event", "is_active"]

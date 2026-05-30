"""
Activity Feed Logger
=====================
Creates real-time system activity log entries in the `activity_logs` collection.
Use this from anywhere in the app to post events to the admin activity feed.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.models.activity_log import ActivityLog
from app.models.user import User

logger = logging.getLogger("app.activity")


async def log_activity(
    event_type: str,
    entity_type: str,
    title: str,
    description: str,
    entity_id: Optional[str] = None,
    actor: Optional[User] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Persist a structured activity event to the activity_logs collection.
    Safe to call everywhere — failures are caught and logged without crashing callers.
    """
    try:
        entry = ActivityLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            title=title,
            description=description,
            actor_id=str(actor.id) if actor else None,
            actor_email=actor.email if actor else None,
            metadata=metadata or {},
        )
        await entry.insert()
    except Exception as e:
        logger.error(f"[ActivityLogger] Failed to write activity log: {e}")

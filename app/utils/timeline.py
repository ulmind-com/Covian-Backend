"""
Candidate Timeline Tracker
===========================
Persists per-candidate lifecycle events to the `candidate_timelines` collection.
Call this whenever something significant happens to a candidate.
"""
import logging
from typing import Any, Dict, Optional

from app.models.candidate_timeline import CandidateTimeline
from app.models.user import User

logger = logging.getLogger("app.timeline")


async def add_candidate_timeline_event(
    candidate_id: str,
    event_type: str,
    title: str,
    description: str,
    actor: Optional[User] = None,
    related_job_id: Optional[str] = None,
    related_application_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Add an event to a candidate's personal timeline.
    Failures are silently logged to avoid cascading errors.
    """
    try:
        entry = CandidateTimeline(
            candidate_id=candidate_id,
            event_type=event_type,
            title=title,
            description=description,
            actor_id=str(actor.id) if actor else None,
            actor_email=actor.email if actor else None,
            related_job_id=related_job_id,
            related_application_id=related_application_id,
            metadata=metadata or {},
        )
        await entry.insert()
    except Exception as e:
        logger.error(f"[Timeline] Failed to write timeline event for candidate {candidate_id}: {e}")

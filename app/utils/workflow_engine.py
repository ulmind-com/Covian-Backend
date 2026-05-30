"""
Workflow Automation Engine
===========================
Triggers active WorkflowRule documents based on platform events.
Evaluates conditions against event payload and executes configured actions.

Usage:
    from app.utils.workflow_engine import trigger_workflow_event
    await trigger_workflow_event("CANDIDATE_STAGE_CHANGED", payload={...}, actor=user)
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.models.workflow import WorkflowRule
from app.models.user import User

logger = logging.getLogger("app.workflow_engine")


async def trigger_workflow_event(
    event: str,
    payload: Dict[str, Any],
    actor: Optional[User] = None
):
    """
    Find all active rules matching the given event trigger,
    evaluate conditions against payload, and execute matched actions.
    """
    try:
        rules = await WorkflowRule.find(
            WorkflowRule.trigger_event == event,
            WorkflowRule.is_active == True
        ).to_list()

        if not rules:
            return

        for rule in rules:
            if _evaluate_conditions(rule.conditions, payload):
                logger.info(f"[WorkflowEngine] Rule '{rule.name}' matched event '{event}'. Executing action: {rule.action_type}")
                await _execute_action(rule, payload, actor)
                # Update rule stats
                rule.last_triggered_at = datetime.now(timezone.utc)
                rule.trigger_count += 1
                rule.updated_at = datetime.now(timezone.utc)
                await rule.save()

    except Exception as e:
        logger.error(f"[WorkflowEngine] Error processing event '{event}': {e}")


def _evaluate_conditions(conditions: Dict[str, Any], payload: Dict[str, Any]) -> bool:
    """
    Check if ALL conditions in the rule match the event payload.
    An empty conditions dict means the rule always fires.
    Supports dot-notation for nested keys (e.g. "stage" matches payload["stage"]).
    """
    if not conditions:
        return True

    for key, expected_value in conditions.items():
        actual_value = payload.get(key)
        # Support list of accepted values
        if isinstance(expected_value, list):
            if actual_value not in expected_value:
                return False
        else:
            if actual_value != expected_value:
                return False
    return True


async def _execute_action(
    rule: WorkflowRule,
    payload: Dict[str, Any],
    actor: Optional[User]
):
    """
    Execute the action specified in the rule.
    Currently supported action_types:
      - SEND_EMAIL
      - CREATE_ACTIVITY_LOG
      - UPDATE_LEAD_SCORE
    """
    action = rule.action_type
    config = rule.action_config

    if action == "SEND_EMAIL":
        await _action_send_email(config, payload)

    elif action == "CREATE_ACTIVITY_LOG":
        await _action_create_activity_log(config, payload, actor)

    elif action == "UPDATE_LEAD_SCORE":
        await _action_update_lead_score(config, payload)

    else:
        logger.warning(f"[WorkflowEngine] Unknown action_type '{action}' in rule '{rule.name}'")


async def _action_send_email(config: Dict, payload: Dict):
    """Enqueue an email notification based on workflow config."""
    try:
        from app.utils.background import enqueue_email_notification
        recipient = config.get("recipient_email") or payload.get(config.get("recipient_field", ""))
        title = config.get("title", "CoreVita Notification")
        # Simple template interpolation using payload values
        message_template = config.get("message", "An automated action was triggered.")
        message = message_template.format(**payload)
        if recipient:
            await enqueue_email_notification(recipient, title, message)
    except Exception as e:
        logger.error(f"[WorkflowEngine] SEND_EMAIL action failed: {e}")


async def _action_create_activity_log(config: Dict, payload: Dict, actor: Optional[User]):
    """Create an activity feed entry from workflow config."""
    try:
        from app.utils.activity import log_activity
        await log_activity(
            event_type=config.get("event_type", "WORKFLOW_TRIGGERED"),
            entity_type=config.get("entity_type", "system"),
            entity_id=payload.get("entity_id"),
            title=config.get("title", "Workflow Action Triggered"),
            description=config.get("description", "An automated workflow action was executed.").format(**payload),
            actor=actor,
            metadata=payload
        )
    except Exception as e:
        logger.error(f"[WorkflowEngine] CREATE_ACTIVITY_LOG action failed: {e}")


async def _action_update_lead_score(config: Dict, payload: Dict):
    """Adjust a lead's score by a given delta when a workflow fires."""
    try:
        from app.models.lead import Lead
        from datetime import timezone
        lead_id = payload.get("lead_id")
        if not lead_id:
            return
        lead = await Lead.get(lead_id)
        if lead:
            delta = int(config.get("score_delta", 10))
            lead.score = max(0, min(100, lead.score + delta))
            lead.last_activity_at = datetime.now(timezone.utc)
            await lead.save()
            logger.info(f"[WorkflowEngine] Lead {lead_id} score updated to {lead.score}")
    except Exception as e:
        logger.error(f"[WorkflowEngine] UPDATE_LEAD_SCORE action failed: {e}")

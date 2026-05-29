from typing import Optional
from fastapi import Request
from app.models.audit_log import AuditLog
from app.models.user import User

async def log_action(
    action: str,
    details: str,
    user: Optional[User] = None,
    request: Optional[Request] = None
):
    """
    Log an administrative or system action into the audit_logs collection.
    """
    ip_address = None
    if request:
        ip_address = request.client.host if request.client else None
        
    log_entry = AuditLog(
        user_id=str(user.id) if user else None,
        user_email=user.email if user else None,
        action=action,
        details=details,
        ip_address=ip_address
    )
    await log_entry.insert()

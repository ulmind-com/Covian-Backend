from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from app.api.deps import get_current_active_user, RoleChecker, PermissionChecker
from app.models.lead import Lead
from app.models.user import User
from app.schemas.platform import LeadCreate, LeadUpdate, LeadResponse
from app.utils.audit import log_action
from app.utils.activity import log_activity
from app.utils.workflow_engine import trigger_workflow_event

router = APIRouter()


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_in: LeadCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Submit or register a new client sales lead.
    Open to any logged-in user.
    """
    if lead_in.assigned_to:
        assignee = await User.get(lead_in.assigned_to)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assigned user ID {lead_in.assigned_to} does not exist."
            )

    lead = Lead(
        company_name=lead_in.company_name,
        contact_name=lead_in.contact_name,
        contact_email=lead_in.contact_email,
        contact_phone=lead_in.contact_phone,
        status=lead_in.status,
        assigned_to=lead_in.assigned_to,
    )
    await lead.insert()
    
    await log_action(
        action="CREATE_LEAD",
        details=f"Created CRM Lead for company: {lead.company_name}",
        user=current_user,
        request=request
    )

    # Log to real-time activity feed
    await log_activity(
        event_type="NEW_LEAD",
        entity_type="lead",
        entity_id=str(lead.id),
        title=f"New lead: {lead.company_name}",
        description=f"CRM lead created for {lead.company_name} (contact: {lead.contact_name}).",
        actor=current_user,
    )

    # Fire workflow engine
    await trigger_workflow_event(
        event="NEW_LEAD",
        payload={
            "lead_id": str(lead.id),
            "company_name": lead.company_name,
            "contact_email": str(lead.contact_email),
            "status": lead.status,
            "assigned_to": lead.assigned_to or "",
        },
        actor=current_user,
    )

    return lead


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "RECRUITER"]))
) -> Any:
    """
    List registered CRM Leads. Supports filtering by status (NEW, CONTACTED, etc.).
    Accessible to admins and recruiters.
    """
    query = {}
    if status_filter:
        query["status"] = status_filter
        
    return await Lead.find(query).skip(skip).limit(limit).to_list()


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead_by_id(
    lead_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "RECRUITER"]))
) -> Any:
    """
    Fetch specific CRM lead by ID.
    """
    lead = await Lead.get(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_in: LeadUpdate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_crm"))
) -> Any:
    """
    Update lead assignment or status.
    Requires 'manage_crm' permission.
    """
    lead = await Lead.get(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
        
    if lead_in.assigned_to:
        assignee = await User.get(lead_in.assigned_to)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assigned user ID {lead_in.assigned_to} does not exist."
            )

    update_data = lead_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
        
    await lead.save()
    
    await log_action(
        action="UPDATE_LEAD",
        details=f"Updated lead: {lead.company_name} (Status: {lead.status}, Assigned: {lead.assigned_to})",
        user=current_user,
        request=request
    )
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_lead(
    lead_id: str,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_crm"))
) -> None:
    """
    Delete a CRM Lead.
    Requires 'manage_crm' permission.
    """
    lead = await Lead.get(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    comp = lead.company_name
    await lead.delete()
    
    await log_action(
        action="DELETE_LEAD",
        details=f"Deleted CRM lead for: {comp} (id: {lead_id})",
        user=current_user,
        request=request
    )
    return None


# ==============================================================================
# LEAD SCORING SYSTEM
# ==============================================================================

@router.get("/leads/scored", response_model=List[LeadResponse])
async def get_scored_leads(
    min_score: int = 0,
    limit: int = 50,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "RECRUITER"]))
) -> Any:
    """
    Return all leads sorted by AI score descending.
    Optionally filter by minimum score threshold using ?min_score=X.
    Scores range 0-100 and auto-update based on status activity.
    """
    all_leads = await Lead.find_all().to_list()
    scored = [l for l in all_leads if l.score >= min_score]
    scored.sort(key=lambda l: l.score, reverse=True)
    return scored[:limit]


@router.post("/leads/{lead_id}/rescore", response_model=LeadResponse)
async def rescore_lead(
    lead_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """
    Manually trigger a lead score recalculation based on current status and activity.
    Scoring rules:
      - Status NEW      : base 10 pts
      - Status CONTACTED: +20 pts
      - Status QUALIFIED: +40 pts
      - Has phone       : +10 pts
      - Has assigned    : +10 pts
      - Score capped at 100
    """
    from datetime import timezone
    lead = await Lead.get(lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    score = 0
    status_scores = {"NEW": 10, "CONTACTED": 30, "QUALIFIED": 70, "LOST": 0}
    score += status_scores.get(lead.status, 0)
    if lead.contact_phone:
        score += 10
    if lead.assigned_to:
        score += 10
    if lead.status == "QUALIFIED":
        score += 10  # bonus for highly qualified

    lead.score = min(100, score)
    from datetime import datetime
    lead.last_activity_at = datetime.now(timezone.utc)
    await lead.save()
    return lead
